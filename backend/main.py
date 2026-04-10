"""
NexaVault – FastAPI Backend
=============================
Entry point for the autonomous trading vault backend.

Endpoints
---------
  GET  /                   – health check
  POST /connect-wallet     – register a wallet address
  POST /trade              – run the full AI → contract → DEX pipeline
  GET  /status             – last trade info + vault state
  GET  /price              – current ALGO/USD price
  POST /deposit            – record a deposit event on-chain
  POST /withdraw           – record a withdrawal event (owner only)

Run with:
    uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
"""

import logging
import os
import time
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Internal modules
from backend.agent import get_agent, Action
from backend.executor import (
    execute_trade_signal, execute_deposit,
    execute_withdraw, get_vault_state,
)
from backend.tinyman_swap import execute_swap
from backend.services.price_feed import get_algo_price
from config.settings import (
    APP_ID, TRADE_AMOUNT_MICROALGO, SLIPPAGE,
    ALLOWED_ORIGINS, LOG_LEVEL,
)

# ─────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger("nexavault.main")

# ─────────────────────────────────────────────
# App + CORS
# ─────────────────────────────────────────────
app = FastAPI(
    title="NexaVault Algo Agent",
    description="Autonomous trading vault on Algorand Testnet",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# In-memory state (replace with Redis/DB in prod)
# ─────────────────────────────────────────────
_state: dict = {
    "connected_wallet" : None,
    "last_trade"       : None,
    "trade_count"      : 0,
    "is_running"       : False,
    "started_at"       : None,
}


# ─────────────────────────────────────────────
# Pydantic request / response models
# ─────────────────────────────────────────────

class WalletConnectRequest(BaseModel):
    address: str
    network: Optional[str] = "testnet"


class TradeRequest(BaseModel):
    wallet_address: Optional[str] = None   # override connected wallet


class DepositRequest(BaseModel):
    amount_microalgo: int


class WithdrawRequest(BaseModel):
    amount_microalgo: int


# ─────────────────────────────────────────────
# Middleware: request logging
# ─────────────────────────────────────────────

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = (time.perf_counter() - start) * 1000
    logger.info("%s %s → %s  (%.1f ms)", request.method, request.url.path,
                response.status_code, elapsed)
    return response


# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────

@app.get("/", tags=["Health"])
async def health():
    """Health check – confirm the API is running."""
    return {
        "status" : "ok",
        "service": "nexavault-algo-agent",
        "app_id" : APP_ID,
        "network": "algorand-testnet",
    }


# ── /connect-wallet ───────────────────────────────────────────────────────────

@app.post("/connect-wallet", tags=["Wallet"])
async def connect_wallet(body: WalletConnectRequest):
    """
    Register a Pera Wallet address with the backend.

    In a real deployment the frontend sends the address after the user
    approves the WalletConnect session; this endpoint just stores it
    so subsequent calls know which account to use.
    """
    if not body.address or len(body.address) < 58:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Algorand address",
        )

    _state["connected_wallet"] = body.address
    logger.info("Wallet connected: %s", body.address)

    return {
        "connected" : True,
        "address"   : body.address,
        "network"   : body.network,
        "app_id"    : APP_ID,
    }


# ── /price ────────────────────────────────────────────────────────────────────

@app.get("/price", tags=["Market"])
async def get_price():
    """Return the latest ALGO/USD price from the price feed."""
    try:
        price_data = await get_algo_price()
        return price_data
    except Exception as exc:
        logger.error("Price fetch error: %s", exc)
        raise HTTPException(status_code=502, detail=f"Price feed error: {exc}")


# ── /trade ────────────────────────────────────────────────────────────────────

@app.post("/trade", tags=["Trading"])
async def run_trade(body: TradeRequest):
    """
    Execute the full autonomous trading pipeline:

    1. Fetch current ALGO/USD price
    2. Run AI agent → "buy" | "sell" | "hold"
    3. If buy/sell → submit ApplicationNoOpTxn to smart contract
    4. If buy/sell → prepare Tinyman swap transactions
    5. Return full result

    This is the core autonomous loop. It can be triggered:
      - Manually from the frontend Dashboard
      - By a scheduler (e.g. APScheduler / cron) for fully automated runs
    """
    wallet = body.wallet_address or _state.get("connected_wallet")
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No wallet connected. Call /connect-wallet first.",
        )

    if APP_ID == 0:
        logger.warning("APP_ID=0 – running in simulation mode (no on-chain calls)")

    try:
        # ── Step 1: Fetch price ─────────────────────────────────────────
        price_data = await get_algo_price()
        logger.info("Price: $%.6f (source=%s)", price_data["price_usd"], price_data["source"])

        # ── Step 2: AI decision ──────────────────────────────────────────
        agent       = get_agent()
        vault_state = await get_vault_state()
        decision    = agent.decide(price_data, vault_state)

        logger.info(
            "Agent decision: action=%s confidence=%.2f reason='%s'",
            decision.action.value, decision.confidence, decision.reason,
        )

        result = {
            "action"         : decision.action.value,
            "confidence"     : decision.confidence,
            "reason"         : decision.reason,
            "price_usd"      : decision.price_usd,
            "price_contract" : decision.price_contract,
            "wallet"         : wallet,
            "timestamp"      : time.time(),
            "contract_txn"   : None,
            "swap"           : None,
        }

        # ── Steps 3 & 4: Execute if actionable ───────────────────────────
        if decision.action != Action.HOLD:

            # 3. On-chain signal
            if APP_ID != 0:
                try:
                    contract_result = await execute_trade_signal(
                        price_contract=decision.price_contract,
                        action=decision.action.value,
                    )
                    result["contract_txn"] = contract_result
                    logger.info("Contract txn confirmed: %s", contract_result)
                except Exception as exc:
                    logger.error("Contract call failed: %s", exc)
                    result["contract_txn"] = {"error": str(exc)}
            else:
                result["contract_txn"] = {"simulated": True}

            # 4. Tinyman swap
            try:
                swap_result = await execute_swap(
                    user_address=wallet,
                    action=decision.action.value,
                    amount_microalgo=TRADE_AMOUNT_MICROALGO,
                    slippage=SLIPPAGE,
                )
                result["swap"] = swap_result
                logger.info("Swap prepared: %s", swap_result.get("quote_summary"))
            except Exception as exc:
                logger.error("Swap preparation failed: %s", exc)
                result["swap"] = {"error": str(exc)}

            _state["trade_count"] += 1

        # ── Persist last trade ────────────────────────────────────────────
        _state["last_trade"] = result

        return result

    except Exception as exc:
        logger.exception("Unexpected error in /trade: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


# ── /status ───────────────────────────────────────────────────────────────────

@app.get("/status", tags=["Trading"])
async def get_status():
    """Return the current vault status and last trade info."""
    vault_state = await get_vault_state()
    return {
        "connected_wallet" : _state.get("connected_wallet"),
        "is_running"       : _state.get("is_running", False),
        "trade_count"      : _state.get("trade_count", 0),
        "last_trade"       : _state.get("last_trade"),
        "vault_state"      : vault_state,
        "app_id"           : APP_ID,
    }


# ── /deposit ──────────────────────────────────────────────────────────────────

@app.post("/deposit", tags=["Vault"])
async def deposit(body: DepositRequest):
    """Record a ALGO deposit into the vault (owner must send ALGO separately)."""
    if body.amount_microalgo <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    if APP_ID == 0:
        return {"simulated": True, "amount": body.amount_microalgo}

    try:
        result = await execute_deposit(body.amount_microalgo)
        logger.info("Deposit recorded on-chain: %s µALGO → txid=%s",
                    body.amount_microalgo, result.get("txid"))
        return result
    except Exception as exc:
        logger.error("Deposit failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


# ── /withdraw ─────────────────────────────────────────────────────────────────

@app.post("/withdraw", tags=["Vault"])
async def withdraw(body: WithdrawRequest):
    """Withdraw ALGO from the vault (owner only – enforced by smart contract)."""
    if body.amount_microalgo <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    if APP_ID == 0:
        return {"simulated": True, "amount": body.amount_microalgo}

    try:
        result = await execute_withdraw(body.amount_microalgo)
        logger.info("Withdrawal approved on-chain: %s µALGO → txid=%s",
                    body.amount_microalgo, result.get("txid"))
        return result
    except Exception as exc:
        logger.error("Withdraw failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
