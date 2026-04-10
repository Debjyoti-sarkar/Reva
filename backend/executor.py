"""
NexaVault – Algorand Transaction Executor
==========================================
Builds, signs, and submits Algorand transactions to the trading vault
smart contract via algosdk.

Key responsibilities
--------------------
* Construct ApplicationNoOpTxn with the correct app arguments
* Sign the transaction (placeholder account for testnet; swap for HSM/KMS in prod)
* Wait for confirmation and return the round + txid

⚠️  TESTNET ONLY – never embed real private keys.
    Use environment variables or a KMS in production.
"""

import base64
import logging
import os
from typing import Optional

from algosdk import account, mnemonic, transaction
from algosdk.v2client import algod

from config.settings import (
    ALGOD_URL, ALGOD_TOKEN, APP_ID,
    WAIT_ROUNDS, TX_NOTE,
)

logger = logging.getLogger("nexavault.executor")


# ─────────────────────────────────────────────
# Algorand client (lazy singleton)
# ─────────────────────────────────────────────

_algod_client: Optional[algod.AlgodClient] = None


def get_algod_client() -> algod.AlgodClient:
    """Return (or create) the shared AlgodClient."""
    global _algod_client
    if _algod_client is None:
        _algod_client = algod.AlgodClient(ALGOD_TOKEN, ALGOD_URL)
        logger.info("AlgodClient initialised → %s", ALGOD_URL)
    return _algod_client


# ─────────────────────────────────────────────
# Key management helpers (TESTNET ONLY)
# ─────────────────────────────────────────────

def _load_private_key() -> tuple[str, str]:
    """
    Load the signing account from environment variables.

    Returns:
        (address, private_key)

    Priority:
      1. VAULT_MNEMONIC  – 25-word BIP-39 mnemonic
      2. VAULT_PRIVATE_KEY – raw base64 private key (for CI)
      3. Auto-generated throwaway key (testnet demos only)

    ⚠️  PRODUCTION: Replace with HSM / AWS KMS / HashiCorp Vault integration.
    """
    mnemo = os.getenv("VAULT_MNEMONIC", "").strip()
    if mnemo:
        pk  = mnemonic.to_private_key(mnemo)
        addr = account.address_from_private_key(pk)
        logger.info("Loaded signing key from VAULT_MNEMONIC → %s", addr)
        return addr, pk

    raw_pk = os.getenv("VAULT_PRIVATE_KEY", "").strip()
    if raw_pk:
        addr = account.address_from_private_key(raw_pk)
        logger.info("Loaded signing key from VAULT_PRIVATE_KEY → %s", addr)
        return addr, raw_pk

    # Throwaway key – for demo / testing only
    pk, addr = account.generate_account()
    logger.warning(
        "⚠️  No key configured – generated throwaway account %s. "
        "Fund it on testnet before submitting real transactions.",
        addr,
    )
    return addr, pk


# ─────────────────────────────────────────────
# Core: submit a NoOp application call
# ─────────────────────────────────────────────

def _encode_args(args: list) -> list:
    """Encode Python values to the byte strings expected by algosdk."""
    encoded = []
    for arg in args:
        if isinstance(arg, str):
            encoded.append(arg.encode())
        elif isinstance(arg, int):
            encoded.append(arg.to_bytes(8, "big"))
        elif isinstance(arg, bytes):
            encoded.append(arg)
        else:
            encoded.append(str(arg).encode())
    return encoded


async def send_noop_txn(
    op: str,
    extra_args: Optional[list] = None,
    app_id: Optional[int] = None,
) -> dict:
    """
    Build and submit an ApplicationNoOpTxn to the vault smart contract.

    Args:
        op         : Operation name passed as args[0], e.g. "trade"
        extra_args : Additional arguments appended after op
        app_id     : Override APP_ID from settings (useful in tests)

    Returns:
        {
            "txid"           : str,
            "confirmed_round": int,
            "op"             : str,
        }
    """
    client  = get_algod_client()
    addr, pk = _load_private_key()
    target_app = app_id or APP_ID

    if target_app == 0:
        raise ValueError(
            "APP_ID is 0 – deploy the contract first and set APP_ID in settings.py"
        )

    # ── Build transaction ────────────────────────────────────────────────
    sp     = client.suggested_params()
    args   = [op] + (extra_args or [])
    enc    = _encode_args(args)
    note   = TX_NOTE.encode() if TX_NOTE else None

    txn = transaction.ApplicationNoOpTxn(
        sender=addr,
        sp=sp,
        index=target_app,
        app_args=enc,
        note=note,
    )

    logger.info("Built NoOp txn: op=%s app_id=%s sender=%s", op, target_app, addr)

    # ── Sign ─────────────────────────────────────────────────────────────
    signed = txn.sign(pk)

    # ── Submit ───────────────────────────────────────────────────────────
    try:
        txid = client.send_transaction(signed)
        logger.info("Submitted txn → txid=%s", txid)
    except Exception as exc:
        logger.error("Failed to submit txn: %s", exc)
        raise

    # ── Wait for confirmation ─────────────────────────────────────────────
    confirmed = transaction.wait_for_confirmation(client, txid, WAIT_ROUNDS)
    round_num = confirmed.get("confirmed-round", 0)
    logger.info("Confirmed in round %s  txid=%s", round_num, txid)

    return {
        "txid"           : txid,
        "confirmed_round": round_num,
        "op"             : op,
    }


# ─────────────────────────────────────────────
# Convenience wrappers
# ─────────────────────────────────────────────

async def execute_trade_signal(price_contract: int, action: str) -> dict:
    """
    Send the AI agent's trade decision to the smart contract.

    Args:
        price_contract : On-chain integer price (USD × 1_000_000)
        action         : "buy" | "sell" | "hold"

    Returns:
        Confirmation dict from send_noop_txn()
    """
    logger.info("execute_trade_signal: action=%s price=%s", action, price_contract)
    result = await send_noop_txn(
        op="trade",
        extra_args=[price_contract],
    )
    result["action"] = action
    return result


async def execute_deposit(amount_microalgo: int) -> dict:
    """
    Record a deposit transaction to the vault smart contract.

    Args:
        amount_microalgo: ALGO amount in microALGO

    Returns:
        Confirmation dict
    """
    logger.info("execute_deposit: %s µALGO", amount_microalgo)
    result = await send_noop_txn(
        op="deposit",
        extra_args=[amount_microalgo],
    )
    result["amount"] = amount_microalgo
    return result


async def execute_withdraw(amount_microalgo: int) -> dict:
    """
    Withdraw ALGO from the vault (owner-gated by smart contract).

    Args:
        amount_microalgo: ALGO amount in microALGO

    Returns:
        Confirmation dict
    """
    logger.info("execute_withdraw: %s µALGO", amount_microalgo)
    result = await send_noop_txn(
        op="withdraw",
        extra_args=[amount_microalgo],
    )
    result["amount"] = amount_microalgo
    return result


async def get_vault_state() -> dict:
    """
    Fetch the current vault state from the smart contract.

    Returns:
        Dict with:
            {
                "buy_price"   : int,
                "sell_price"  : int,
                "last_price"  : int,
                "last_action" : str,
                "trade_count" : int,
                "owner"       : str,
            }
    """
    if APP_ID == 0:
        return {
            "buy_price": 150_000_000,
            "sell_price": 220_000_000,
            "last_price": 0,
            "last_action": "none",
            "trade_count": 0,
            "owner": "N/A (APP_ID=0)",
        }

    try:
        client = get_algod_client()
        app_info = client.application_info(APP_ID)
        state = app_info.get("params", {}).get("global-state", [])

        result = {}
        for item in state:
            key = item.get("key")
            if isinstance(key, str):
                key = key
            val = item.get("value", {})

            if key == "buy_price":
                result["buy_price"] = val.get("uint", 0)
            elif key == "sell_price":
                result["sell_price"] = val.get("uint", 0)
            elif key == "last_price":
                result["last_price"] = val.get("uint", 0)
            elif key == "last_action":
                import base64
                result["last_action"] = (
                    base64.b64decode(val.get("bytes", "")).decode()
                    if val.get("bytes")
                    else "unknown"
                )
            elif key == "trade_count":
                result["trade_count"] = val.get("uint", 0)
            elif key == "owner":
                import base64
                result["owner"] = (
                    base64.b64decode(val.get("bytes", "")).decode()
                    if val.get("bytes")
                    else "unknown"
                )

        logger.info("Vault state fetched: %s", result)
        return result

    except Exception as exc:
        logger.error("Failed to fetch vault state: %s", exc)
        return {"error": str(exc)}


async def execute_deposit(amount_microalgo: int) -> dict:
    """Record a deposit event on-chain."""
    return await send_noop_txn(op="deposit", extra_args=[amount_microalgo])


async def execute_withdraw(amount_microalgo: int) -> dict:
    """Record a withdrawal event on-chain (owner-gated)."""
    return await send_noop_txn(op="withdraw", extra_args=[amount_microalgo])


async def get_vault_state() -> dict:
    """
    Read the current global state of the vault smart contract.

    Returns a human-readable dict of all global state keys.
    """
    client = get_algod_client()
    if APP_ID == 0:
        return {"error": "APP_ID not configured"}

    try:
        app_info = client.application_info(APP_ID)
        raw_state = app_info["params"]["global-state"]
    except Exception as exc:
        logger.error("Failed to fetch vault state: %s", exc)
        return {"error": str(exc)}

    state = {}
    for item in raw_state:
        key_b64 = item["key"]
        key     = base64.b64decode(key_b64).decode("utf-8", errors="replace")
        val     = item["value"]
        if val["type"] == 1:    # bytes
            state[key] = base64.b64decode(val["bytes"]).decode("utf-8", errors="replace")
        else:                   # uint
            state[key] = val["uint"]

    logger.debug("Vault state: %s", state)
    return state
