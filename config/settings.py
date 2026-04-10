"""
NexaVault – Configuration Settings
=====================================
All environment-configurable settings in one place.

Environment variables override these defaults.
Never commit real private keys – use .env files locally
and secrets managers (AWS Secrets Manager, Vault) in production.
"""

import os


# ─────────────────────────────────────────────
# Algorand Node
# ─────────────────────────────────────────────
ALGOD_URL   = os.getenv("ALGOD_URL",   "https://testnet-api.algonode.cloud")
ALGOD_TOKEN = os.getenv("ALGOD_TOKEN", "")          # Algonode is open – no token needed

INDEXER_URL   = os.getenv("INDEXER_URL",   "https://testnet-idx.algonode.cloud")
INDEXER_TOKEN = os.getenv("INDEXER_TOKEN", "")

# ─────────────────────────────────────────────
# Smart Contract
# ─────────────────────────────────────────────
APP_ID = int(os.getenv("APP_ID", "0"))              # 0 = not deployed yet

# ─────────────────────────────────────────────
# Vault Signing Account  (TESTNET ONLY)
# ─────────────────────────────────────────────
# Option A: 25-word mnemonic
VAULT_MNEMONIC     = os.getenv("VAULT_MNEMONIC",     "")
# Option B: raw base64 private key
VAULT_PRIVATE_KEY  = os.getenv("VAULT_PRIVATE_KEY",  "")
# Readable wallet address (informational – derived from key above)
WALLET_ADDRESS     = os.getenv("WALLET_ADDRESS",     "PLACEHOLDER_ADDRESS")

# ─────────────────────────────────────────────
# Trading Parameters
# ─────────────────────────────────────────────
# Trade size per cycle in microALGO (default: 1 ALGO)
TRADE_AMOUNT_MICROALGO = int(os.getenv("TRADE_AMOUNT_MICROALGO", str(1_000_000)))

# Buy/sell thresholds in USD (used by RuleBasedStrategy)
BUY_THRESHOLD_USD  = float(os.getenv("BUY_THRESHOLD_USD",  "0.15"))
SELL_THRESHOLD_USD = float(os.getenv("SELL_THRESHOLD_USD", "0.22"))

# Tinyman slippage tolerance (1% default)
SLIPPAGE = float(os.getenv("SLIPPAGE", "0.01"))

# ─────────────────────────────────────────────
# Tinyman
# ─────────────────────────────────────────────
# Tinyman V2 Testnet validator app ID
TINYMAN_VALIDATOR_APP_ID = int(os.getenv("TINYMAN_VALIDATOR_APP_ID", "1002541853"))

# Test USDC on Algorand Testnet (asset 10458941 from GoFundMe / Testnet dispensers)
USDC_ASSET_ID = int(os.getenv("USDC_ASSET_ID", "10458941"))

# ─────────────────────────────────────────────
# Transaction
# ─────────────────────────────────────────────
WAIT_ROUNDS = int(os.getenv("WAIT_ROUNDS", "4"))    # rounds to wait for confirmation
TX_NOTE     = os.getenv("TX_NOTE", "NexaVault auto-trade")

# ─────────────────────────────────────────────
# AI Agent
# ─────────────────────────────────────────────
AGENT_STRATEGY = os.getenv("AGENT_STRATEGY", "rule")  # "rule" | "ml"
MODEL_PATH     = os.getenv("MODEL_PATH", "models/nexavault_agent.pkl")

# ─────────────────────────────────────────────
# Price Feed
# ─────────────────────────────────────────────
USE_MOCK_PRICE = os.getenv("USE_MOCK_PRICE", "false").lower() == "true"

# ─────────────────────────────────────────────
# FastAPI / CORS
# ─────────────────────────────────────────────
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000",
).split(",")

# ─────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
