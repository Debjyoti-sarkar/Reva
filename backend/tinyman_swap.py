"""
NexaVault – Tinyman DEX Swap Module
=====================================
Wraps the tinyman-py-sdk to:
  1. Connect to Tinyman V2 on Algorand Testnet
  2. Fetch the ALGO/USDC pool
  3. Generate a swap quote
  4. Prepare the unsigned transaction group

The caller (executor.py or /trade endpoint) is responsible for
collecting signatures and submitting the group.

Tinyman V2 Testnet pool registry:
  https://testnet.tinyman.org/#/swap

⚠️  TESTNET ONLY – pool IDs differ on mainnet.
"""

import logging
import os
from typing import Optional

# tinyman-py-sdk  (pip install tinyman-py-sdk)
try:
    from tinyman.v2.client import TinymanV2TestnetClient
    from tinyman.utils import TransactionGroup
    TINYMAN_AVAILABLE = True
except ImportError:
    TINYMAN_AVAILABLE = False

from algosdk.v2client import algod

from config.settings import ALGOD_URL, ALGOD_TOKEN, TINYMAN_VALIDATOR_APP_ID
from backend.executor import get_algod_client

logger = logging.getLogger("nexavault.tinyman_swap")

# ── Asset IDs (Algorand Testnet) ─────────────────────────────────────────────
ALGO_ASSET_ID  = 0          # ALGO is represented as asset 0 (or 1 in some SDKs)
# USDC on Algorand Testnet (GoFundMe / test USDC)
USDC_ASSET_ID  = int(os.getenv("USDC_ASSET_ID", "10458941"))


# ─────────────────────────────────────────────
# Client singleton
# ─────────────────────────────────────────────

_tinyman_client = None


def get_tinyman_client():
    """Return (or create) the shared Tinyman testnet client."""
    global _tinyman_client
    if _tinyman_client is None:
        if not TINYMAN_AVAILABLE:
            raise ImportError(
                "tinyman-py-sdk is not installed. "
                "Run: pip install tinyman-py-sdk"
            )
        algod_client = get_algod_client()
        _tinyman_client = TinymanV2TestnetClient(
            algod_client=algod_client,
            user_address=None,              # set per-swap below
        )
        logger.info("TinymanV2TestnetClient initialised")
    return _tinyman_client


# ─────────────────────────────────────────────
# Fetch pool
# ─────────────────────────────────────────────

async def fetch_algo_usdc_pool():
    """
    Fetch the ALGO/USDC liquidity pool from Tinyman Testnet.

    Returns:
        Tinyman Pool object, or None on failure.
    """
    if not TINYMAN_AVAILABLE:
        logger.error("tinyman-py-sdk not available – skipping pool fetch")
        return None

    client = get_tinyman_client()
    try:
        pool = client.fetch_pool(ALGO_ASSET_ID, USDC_ASSET_ID)
        logger.info(
            "Pool fetched: %s  liquidity=%s",
            pool.address,
            getattr(pool, "liquidity", "unknown"),
        )
        return pool
    except Exception as exc:
        logger.error("Failed to fetch ALGO/USDC pool: %s", exc)
        return None


# ─────────────────────────────────────────────
# Generate swap quote
# ─────────────────────────────────────────────

async def get_swap_quote(
    action: str,
    amount_microalgo: int,
    slippage: float = 0.01,
) -> Optional[dict]:
    """
    Generate a swap quote for buying or selling ALGO.

    Args:
        action          : "buy" (USDC → ALGO) or "sell" (ALGO → USDC)
        amount_microalgo: Amount of ALGO in microALGO (1 ALGO = 1_000_000 µALGO)
        slippage        : Maximum allowed slippage (default 1%)

    Returns:
        {
            "input_asset_id"  : int,
            "output_asset_id" : int,
            "input_amount"    : int,
            "output_amount"   : int,   # minimum guaranteed after slippage
            "price_impact"    : float,
            "quote"           : object (raw Tinyman quote for tx preparation)
        }
        or None on failure.
    """
    pool = await fetch_algo_usdc_pool()
    if pool is None:
        return None

    try:
        algo_asset = pool.asset1 if pool.asset1.id == ALGO_ASSET_ID else pool.asset2
        usdc_asset = pool.asset1 if pool.asset1.id == USDC_ASSET_ID else pool.asset2

        if action == "sell":
            # Selling ALGO for USDC: exact_input = ALGO amount
            input_asset  = algo_asset
            output_asset = usdc_asset
            input_amount = amount_microalgo
        else:
            # Buying ALGO with USDC: use fixed output swap
            input_asset  = usdc_asset
            output_asset = algo_asset
            input_amount = amount_microalgo   # treated as micro-USDC equivalent

        quote = pool.fetch_fixed_input_swap_quote(
            amount_in=input_asset(input_amount),
            slippage=slippage,
        )

        result = {
            "input_asset_id"  : input_asset.id,
            "output_asset_id" : output_asset.id,
            "input_amount"    : input_amount,
            "output_amount"   : int(quote.amount_out_with_slippage),
            "price_impact"    : float(getattr(quote, "price_impact", 0.0)),
            "quote"           : quote,
        }

        logger.info(
            "Quote [%s]: in=%s µ%s  out≥%s µ%s  impact=%.4f%%",
            action,
            result["input_amount"],
            "ALGO" if action == "sell" else "USDC",
            result["output_amount"],
            "USDC" if action == "sell" else "ALGO",
            result["price_impact"] * 100,
        )
        return result

    except Exception as exc:
        logger.error("Failed to generate swap quote: %s", exc)
        return None


# ─────────────────────────────────────────────
# Prepare transaction group
# ─────────────────────────────────────────────

async def prepare_swap_transactions(
    user_address: str,
    action: str,
    amount_microalgo: int,
    slippage: float = 0.01,
) -> Optional[dict]:
    """
    Prepare the Tinyman swap transaction group (unsigned).

    Args:
        user_address    : Algorand address executing the swap
        action          : "buy" or "sell"
        amount_microalgo: ALGO amount in microALGO
        slippage        : Maximum slippage tolerance

    Returns:
        {
            "transactions": list of base64-encoded unsigned transactions,
            "txids"       : list of expected txids,
            "quote_summary": dict with human-readable quote info,
        }
        or None on failure.
    """
    pool = await fetch_algo_usdc_pool()
    if pool is None:
        return None

    quote_data = await get_swap_quote(action, amount_microalgo, slippage)
    if quote_data is None:
        return None

    quote = quote_data["quote"]

    try:
        # Build unsigned transaction group
        txn_group: TransactionGroup = pool.prepare_swap_transactions(
            amount_in=pool.asset1(quote_data["input_amount"])
                      if quote_data["input_asset_id"] == pool.asset1.id
                      else pool.asset2(quote_data["input_amount"]),
            amount_out=pool.asset1(quote_data["output_amount"])
                       if quote_data["output_asset_id"] == pool.asset1.id
                       else pool.asset2(quote_data["output_amount"]),
            swap_type="fixed-input",
            swapper_address=user_address,
        )

        # Encode each unsigned txn as base64 for the frontend to sign
        import base64
        encoded_txns = []
        for txn in txn_group.transactions:
            encoded_txns.append(
                base64.b64encode(txn.serialize()).decode()
            )

        return {
            "transactions": encoded_txns,
            "txids"       : [t.get_txid() for t in txn_group.transactions],
            "quote_summary": {
                "action"        : action,
                "input_amount"  : quote_data["input_amount"],
                "output_amount" : quote_data["output_amount"],
                "price_impact"  : quote_data["price_impact"],
                "slippage"      : slippage,
            },
        }

    except Exception as exc:
        logger.error("Failed to prepare swap transactions: %s", exc)
        return None


# ─────────────────────────────────────────────
# Mock swap (when Tinyman is unavailable)
# ─────────────────────────────────────────────

async def mock_swap(action: str, amount_microalgo: int) -> dict:
    """
    Return a simulated swap result for local development / CI.
    Used automatically when TINYMAN_AVAILABLE is False.
    """
    logger.warning("Using MOCK swap – Tinyman SDK not available")
    import random
    mock_price = 0.175
    if action == "sell":
        out = int(amount_microalgo * mock_price * (1 + random.uniform(-0.01, 0.01)))
    else:
        out = int((amount_microalgo / mock_price) * (1 + random.uniform(-0.01, 0.01)))

    return {
        "mock"          : True,
        "action"        : action,
        "input_amount"  : amount_microalgo,
        "output_amount" : out,
        "price_impact"  : 0.0,
        "transactions"  : [],
        "txids"         : [],
    }


async def execute_swap(
    user_address: str,
    action: str,
    amount_microalgo: int,
    slippage: float = 0.01,
) -> dict:
    """
    High-level entry point: prepare a real swap or return mock if unavailable.

    Args:
        user_address    : Signer's Algorand address
        action          : "buy" | "sell"
        amount_microalgo: Trade size in microALGO
        slippage        : Max slippage

    Returns:
        Swap result dict (see prepare_swap_transactions or mock_swap)
    """
    if not TINYMAN_AVAILABLE:
        return await mock_swap(action, amount_microalgo)

    result = await prepare_swap_transactions(
        user_address, action, amount_microalgo, slippage
    )
    if result is None:
        logger.warning("Swap preparation failed – falling back to mock")
        return await mock_swap(action, amount_microalgo)

    return result
