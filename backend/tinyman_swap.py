"""
NexaVault – Tinyman DEX Swap Module (FIXED)
"""

import logging
import os
from typing import Optional

# Tinyman SDK
try:
    from tinyman.v2.client import TinymanV2TestnetClient
    from tinyman.utils import TransactionGroup
    TINYMAN_AVAILABLE = True
except ImportError:
    TINYMAN_AVAILABLE = False

from backend.executor import get_algod_client

logger = logging.getLogger("nexavault.tinyman_swap")

# ── Asset IDs ─────────────────────────────────────────────
ALGO_ASSET_ID = 0
USDC_ASSET_ID = int(os.getenv("USDC_ASSET_ID", "10458941"))

# ── Client Singleton ──────────────────────────────────────
_tinyman_client = None


def get_tinyman_client():
    global _tinyman_client

    if _tinyman_client is None:
        if not TINYMAN_AVAILABLE:
            raise ImportError("tinyman-py-sdk not installed")

        algod_client = get_algod_client()
        _tinyman_client = TinymanV2TestnetClient(
            algod_client=algod_client,
            user_address=None,
        )
        logger.info("Tinyman client initialized")

    return _tinyman_client


# ── Fetch Pool ────────────────────────────────────────────
async def fetch_algo_usdc_pool():
    if not TINYMAN_AVAILABLE:
        return None

    client = get_tinyman_client()

    try:
        pool = client.fetch_pool(ALGO_ASSET_ID, USDC_ASSET_ID)
        return pool
    except Exception as e:
        logger.error("Pool fetch failed: %s", e)
        return None


# ── Swap Quote ────────────────────────────────────────────
async def get_swap_quote(action: str, amount_microalgo: int, slippage: float = 0.01):
    pool = await fetch_algo_usdc_pool()

    if not pool:
        return None

    try:
        algo = pool.asset1 if pool.asset1.id == ALGO_ASSET_ID else pool.asset2
        usdc = pool.asset1 if pool.asset1.id == USDC_ASSET_ID else pool.asset2

        if action == "sell":
            input_asset = algo
            output_asset = usdc
        else:
            input_asset = usdc
            output_asset = algo

        quote = pool.fetch_fixed_input_swap_quote(
            amount_in=input_asset(amount_microalgo),
            slippage=slippage,
        )

        return {
            "input_asset_id": input_asset.id,
            "output_asset_id": output_asset.id,
            "input_amount": amount_microalgo,
            "output_amount": int(quote.amount_out_with_slippage),
            "price_impact": float(getattr(quote, "price_impact", 0.0)),
            "quote": quote,
        }

    except Exception as e:
        logger.error("Quote failed: %s", e)
        return None


# ── Prepare Transactions ──────────────────────────────────
async def prepare_swap_transactions(user_address, action, amount_microalgo, slippage=0.01):
    pool = await fetch_algo_usdc_pool()

    if not pool:
        return None

    quote_data = await get_swap_quote(action, amount_microalgo, slippage)

    if not quote_data:
        return None

    try:
        txn_group: TransactionGroup = pool.prepare_swap_transactions(
            amount_in=pool.asset1(quote_data["input_amount"]),
            swap_type="fixed-input",
            swapper_address=user_address,
        )

        import base64

        encoded = [
            base64.b64encode(txn.serialize()).decode()
            for txn in txn_group.transactions
        ]

        return {
            "transactions": encoded,
            "txids": [t.get_txid() for t in txn_group.transactions],
            "quote_summary": quote_data,
        }

    except Exception as e:
        logger.error("Txn prep failed: %s", e)
        return None


# ── Mock Swap ─────────────────────────────────────────────
async def mock_swap(action, amount_microalgo):
    import random

    price = 0.17

    if action == "sell":
        out = int(amount_microalgo * price)
    else:
        out = int(amount_microalgo / price)

    return {
        "mock": True,
        "action": action,
        "input_amount": amount_microalgo,
        "output_amount": out,
        "transactions": [],
        "txids": [],
    }


# ── Execute Swap ──────────────────────────────────────────
async def execute_swap(user_address, action, amount_microalgo, slippage=0.01):
    if not TINYMAN_AVAILABLE:
        return await mock_swap(action, amount_microalgo)

    result = await prepare_swap_transactions(
        user_address, action, amount_microalgo, slippage
    )

    if result is None:
        logger.warning("Fallback to mock swap")
        return await mock_swap(action, amount_microalgo)

    logger.info("Swap ready")
    return result