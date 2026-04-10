# NexaVault – Complete Setup & Run Guide

**Autonomous AI-Powered Algorand Trading Vault**

🎯 **Goal**: Run a fully functional end-to-end trading system on Algorand Testnet with AI-powered buy/sell decisions, Pera Wallet integration, and Tinyman DEX swaps.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Architecture Overview](#architecture-overview)
3. [Setup Steps](#setup-steps)
4. [Running the System](#running-the-system)
5. [Testing the System](#testing-the-system)
6. [API Reference](#api-reference)
7. [Troubleshooting](#troubleshooting)
8. [Configuration Options](#configuration-options)

---

## Prerequisites

### Required Software

- **Python 3.9+** – [Download from python.org](https://www.python.org/downloads/)
- **Node.js 16+** (for React frontend) – [Download from nodejs.org](https://nodejs.org/)
- **PowerShell 5.0+** (Windows) – Usually pre-installed
- **Git** (optional, for version control)

### Required Knowledge

- Basic familiarity with command-line/terminal
- Understanding of Algorand, wallets, and testnet concepts
- (Optional) Basic understanding of trading/market making

### Testnet Account

You'll need a funded Algorand Testnet account:

1. **Create a new account** (if you don't have one):
   ```powershell
   cd C:\Users\YourUsername\Desktop\lkj\Reva
   python -c "from algosdk import account, mnemonic; pk, addr = account.generate_account(); print(f'Address: {addr}'); print(f'Mnemonic: {mnemonic.from_private_key(pk)}'); print(f'Private Key: {pk}')"
   ```

2. **Fund the account** with at least **2 ALGO** (0.5 for deployment + 1.5 for trading):
   - 🔗 [Algorand Testnet Faucet](https://bank.testnet.algorand.network/)
   - Save your **25-word mnemonic** securely

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Browser (React)                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Dashboard                                                │   │
│  │  • Connect Pera Wallet                                   │   │
│  │  • View ALGO/USD price                                   │   │
│  │  • Show AI decision (buy/sell/hold)                      │   │
│  │  • Start/stop auto trading                               │   │
│  │  • View trade history                                    │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ /price       → Fetch live ALGO/USD from CoinGecko        │   │
│  │ /trade       → Run AI agent → execute on-chain           │   │
│  │ /status      → Return vault state & trade history        │   │
│  │ /deposit     → Record deposits                            │   │
│  │ /withdraw    → Withdraw funds (owner only)                │   │
│  └──────────────────────────────────────────────────────────┘   │
│                             │                                   │
│  ┌────────────┘─────────────┴─────────────┐                   │
│  │                    │                    │                   │
│  ▼                    ▼                    ▼                   │
│ ┌──────────┐    ┌──────────┐    ┌──────────────────┐          │
│ │ AI Agent │    │  Price   │    │  Tinyman Swap    │          │
│ │ (Rule-   │    │  Feed    │    │  Preparation     │          │
│ │  based)  │    │          │    │                  │          │
│ └──────────┘    └──────────┘    └──────────────────┘          │
└────────────────────────────────────────────────────────────────┘
                      │
                      │ Algorand SDK
                      ▼
┌────────────────────────────────────────────────────────────────┐
│              Algorand Testnet                                   │
│  ┌──────────────────────────────────────┐                      │
│  │ Smart Contract (PyTeal)               │                     │
│  │ ├─ Handle trade signals               │                     │
│  │ ├─ Update buy/sell thresholds         │                     │
│  │ ├─ Record trade history               │                     │
│  │ └─ Gate deposits/withdrawals          │                     │
│  └──────────────────────────────────────┘                      │
│           │                      │                              │
│           ▼                      ▼                              │
│  ┌──────────────────┐  ┌────────────────────┐                 │
│  │ Vault Balance    │  │ Trade Thresholds   │                 │
│  │ (Managed ALGO)   │  │ (Buy/Sell prices)  │                 │
│  └──────────────────┘  └────────────────────┘                 │
└────────────────────────────────────────────────────────────────┘
          │
          │ Swap via
          │ Tinyman
          ▼
   ┌─────────────────┐
   │ ALGO ⇄ USDC     │
   │ on Tinyman V2   │
   └─────────────────┘
```

---

## Setup Steps

### Step 1: Run the Automated Setup Script

The easiest way to get started is using the provided PowerShell script:

```powershell
cd C:\Users\DebSarkar\Desktop\lkj\Reva
.\SETUP.ps1
```

This script will:
1. ✅ Create a Python virtual environment
2. ✅ Install backend dependencies
3. ✅ Guide you through account setup
4. ✅ Deploy the smart contract
5. ✅ Install frontend dependencies
6. ✅ Provide run instructions

**OR**, follow the manual steps below:

### Step 2: Manual Setup (if not using the script)

#### 2.1 Create Python Virtual Environment

```powershell
cd C:\Users\DebSarkar\Desktop\lkj\Reva
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

#### 2.2 Install Python Dependencies

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

Expected output:
```
Successfully installed fastapi uvicorn algosdk pyteal tinyman-py-sdk pydantic httpx python-dotenv
```

#### 2.3 Create/Update .env File

Edit or create `C:\Users\DebSarkar\Desktop\lkj\Reva\.env`:

```env
# Algorand Testnet node (Algonode is free and no token needed)
ALGOD_URL=https://testnet-api.algonode.cloud
ALGOD_TOKEN=

# Your funded testnet account's MNEMONIC (25 words)
VAULT_MNEMONIC=your twenty five word seed phrase here...

# Smart contract ID (will be set after deployment)
APP_ID=0

# Trading parameters
BUY_THRESHOLD_USD=0.15
SELL_THRESHOLD_USD=0.22
TRADE_AMOUNT_MICROALGO=1000000

# Use mock price or live CoinGecko data
USE_MOCK_PRICE=false
```

⚠️ **IMPORTANT**: Never commit `.env` to version control – it contains your private key!

#### 2.4 Verify Backend Setup

```powershell
python -c "from backend.main import app; print('✅ Backend imports OK')"
```

Expected output:
```
✅ Backend imports OK
```

#### 2.5 Deploy Smart Contract to Testnet

```powershell
python scripts/deploy_contract.py
```

Expected output:
```
🚀 Deploying from WNQD3...XXXXXX ...
💰 Account balance: 2.5000 ALGO
🔧 Compiling PyTeal → TEAL ...
✅ TEAL files written to contracts/
🔧 Compiling TEAL via algod ...
✅ Bytecode compiled
📤 Submitted deploy txn: XXXXXXX
✅ Contract deployed successfully!
   APP_ID  : 123456789
   TxID    : XXXXXXX
   Round   : 28950000
=====================================
🔑 Add this to your .env or config/settings.py:
   APP_ID=123456789
```

**👉 Copy the `APP_ID` value and update your `.env` file:**

```env
APP_ID=123456789  # Replace with your actual APP_ID
```

#### 2.6 Setup Frontend

```powershell
cd frontend
npm install
cd ..
```

### Step 3: Verify All Components

```powershell
# Test Python imports
python -c "
from backend.main import app
from backend.agent import get_agent
from backend.executor import get_algod_client
from backend.tinyman_swap import get_tinyman_client
from backend.services.price_feed import get_algo_price
print('✅ All Python modules imported successfully')
"

# Test Node.js
node -v  # Should be v16+ 
npm -v   # Should be 8+
```

---

## Running the System

### Run Backend (Terminal 1)

```powershell
cd C:\Users\DebSarkar\Desktop\lkj\Reva
.\.venv\Scripts\Activate.ps1
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started server process [12345]
```

✅ Backend is running – Test it:
```powershell
# In a new PowerShell window
curl http://localhost:8000/
# Should return: {"status":"ok","service":"nexavault-algo-agent",...}
```

### Run Frontend (Terminal 2)

```powershell
cd C:\Users\DebSarkar\Desktop\lkj\Reva\frontend
npm start
```

**Expected output:**
```
Compiled successfully!

You can now view nexavault-frontend in the browser.

  Local:          http://localhost:3000
  On Your Network: http://192.168.X.X:3000
Note that the development build is not optimized.
To create a production build, use npm run build.
```

✅ Frontend is running at http://localhost:3000

---

## Testing the System

### Test 1: Verify Backend API

```powershell
# Health check
curl http://localhost:8000/

# Get current price
curl http://localhost:8000/price

# Get vault status
curl http://localhost:8000/status
```

### Test 2: Verify Smart Contract

```powershell
python -c "
import asyncio
from backend.executor import get_vault_state

async def test():
    state = await get_vault_state()
    print('Vault state:', state)

asyncio.run(test())
"
```

### Test 3: Test Frontend (Manual)

1. Open http://localhost:3000
2. Click "Connect Pera Wallet"
3. Scan the QR code with Pera Wallet mobile app
4. Approve the connection
5. Click "▶ Start Auto Trading"
6. Watch the dashboard for trades

### Test 4: Trigger a Manual Trade

```powershell
# Get your wallet address from Pera Wallet first
$WALLET = "YOUR_WALLET_ADDRESS_HERE"

curl -X POST http://localhost:8000/trade `
  -H "Content-Type: application/json" `
  -d "{`"wallet_address`":`"$WALLET`"}"
```

---

## API Reference

### Health Check
```
GET /
Response: {"status":"ok","service":"nexavault-algo-agent","app_id":123456789,network":"algorand-testnet"}
```

### Get Current Price
```
GET /price
Response: {
  "price_usd": 0.175,
  "price_contract": 175000,
  "source": "coingecko"
}
```

### Execute Trade
```
POST /trade
Body: {"wallet_address": "XXXXXXX..."}
Response: {
  "action": "buy",
  "confidence": 0.85,
  "reason": "Price $0.15 ≤ buy threshold $0.15...",
  "price_usd": 0.15,
  "price_contract": 150000,
  "contract_txn": {"txid": "...", "confirmed_round": 28950000},
  "swap": {"transactions": [...], "quote_summary": {...}}
}
```

### Get Status
```
GET /status
Response: {
  "connected_wallet": "XXXXXXX...",
  "is_running": false,
  "trade_count": 5,
  "last_trade": {...},
  "vault_state": {"buy_price": 150000000, ...},
  "app_id": 123456789
}
```

### Connect Wallet
```
POST /connect-wallet
Body: {"address": "XXXXXXX...", "network": "testnet"}
Response: {"connected": true, "address": "XXXXXXX...", "app_id": 123456789}
```

### Deposit
```
POST /deposit
Body: {"amount_microalgo": 1000000}
Response: {"txid": "...", "amount": 1000000}
```

### Withdraw
```
POST /withdraw
Body: {"amount_microalgo": 1000000}
Response: {"txid": "...", "amount": 1000000}
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'algosdk'"

**Solution:**
```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Issue: "VAULT_MNEMONIC not set" or "APP_ID is 0"

**Solution:** Check your `.env` file is in the correct location:
```powershell
Test-Path C:\Users\DebSarkar\Desktop\lkj\Reva\.env
cat .env | grep VAULT_MNEMONIC
cat .env | grep APP_ID
```

### Issue: "Connection refused" or "Address already in use" on port 8000

**Solution:** Another process is using port 8000. Either:
1. Kill the process: `netstat -ano | findstr :8000`
2. Use a different port: `uvicorn backend.main:app --port 8001`

### Issue: "Insufficient balance" during contract deployment

**Solution:** You need at least 1 ALGO in your account:
1. Go to https://bank.testnet.algorand.network/
2. Paste your address and fund with 2+ ALGO
3. Wait a few seconds for confirmation
4. Retry deployment

### Issue: Pera Wallet connection fails or QR code doesn't work

**Solution:**
1. Ensure you have Pera Wallet mobile app installed on your phone
2. Check you're on Testnet in Pera Wallet settings
3. Ensure your phone and computer are on the same network (or adjust CORS)
4. Try using the deeplink instead of QR (Pera app usually detects automatically)

### Issue: "tinyman-py-sdk not installed"

**Solution:**
```powershell
.\.venv\Scripts\Activate.ps1
pip install tinyman-py-sdk
```

### Issue: Price feed returns 0 or error

**Solution:** This is normal for `USE_MOCK_PRICE=true`. If using live prices:
```powershell
# Test CoinGecko API manually
curl "https://api.coingecko.com/api/v3/simple/price?ids=algorand&vs_currencies=usd"
```

If the API is down, set `USE_MOCK_PRICE=true` in `.env`.

---

## Configuration Options

### Agent Strategy

**Rule-Based (Default)**
```env
AGENT_STRATEGY=rule
BUY_THRESHOLD_USD=0.15
SELL_THRESHOLD_USD=0.22
```

Buys when price ≤ $0.15, sells when ≥ $0.22, holds otherwise.

**Machine Learning (Optional)**
```env
AGENT_STRATEGY=ml
MODEL_PATH=models/my_model.pkl
```

Requires a pre-trained scikit-learn/FinRL model.

### Price Feed

**Live Prices (Default)**
```env
USE_MOCK_PRICE=false
```

Fetches real ALGO/USD price from CoinGecko API. Requires internet access.

**Mock Prices (Development)**
```env
USE_MOCK_PRICE=true
```

Simulates realistic price movements using a sine wave. Useful for local development without internet.

### Tinyman Swap

```env
TINYMAN_VALIDATOR_APP_ID=1002541853  # Testnet validator
USDC_ASSET_ID=10458941               # Test USDC on Testnet
SLIPPAGE=0.01                        # 1% maximum slippage
```

### Logging

```env
LOG_LEVEL=INFO
# Options: DEBUG (very verbose), INFO (normal), WARNING, ERROR
```

---

## Advanced Topics

### Using a Custom ML Model

1. Train your model externally using FinRL or scikit-learn
2. Save it as `models/my_model.pkl`
3. Set `AGENT_STRATEGY=ml` and `MODEL_PATH=models/my_model.pkl`
4. The agent will automatically use your model with fallback to rule-based if inference fails

### Running with Production Database

Replace in-memory state with Redis or PostgreSQL:

```python
# In backend/main.py, replace `_state` dict with your DB client
import redis
r = redis.Redis(host='localhost', port=6379, db=0)
```

### Deploying to Production

1. Set environment variables in production environment (not .env)
2. Use real private key management (AWS Secrets Manager, HashiCorp Vault)
3. Use production Algorand nodes (not Algonode, use your own or a paid provider)
4. Add rate limiting, authentication, and HTTPS
5. Use systemd/PM2 to keep services running
6. Add monitoring and alerting

---

## Key Files

| File | Purpose |
|------|---------|
| `backend/main.py` | FastAPI app with all endpoints |
| `backend/agent.py` | AI trading logic (rule-based + ML) |
| `backend/executor.py` | Transaction execution on Algorand |
| `backend/tinyman_swap.py` | Tinyman DEX swap integration |
| `contracts/trading_vault.py` | Smart contract (PyTeal) |
| `scripts/deploy_contract.py` | Deployment script |
| `frontend/src/App.jsx` | React root component |
| `frontend/src/Dashboard.jsx` | Main trading dashboard |
| `frontend/src/peraConnect.js` | Pera Wallet integration |
| `.env` | Environment configuration (NEVER commit!) |
| `requirements.txt` | Python dependencies |
| `frontend/package.json` | JavaScript dependencies |

---

## Documentation Links

- 📚 **Algorand SDK**: https://py-algorand-sdk.readthedocs.io/
- 🧬 **PyTeal Docs**: https://pyteal.readthedocs.io/
- 🔗 **Pera Wallet Connect**: https://github.com/perawallet/connect
- 🔄 **Tinyman SDK**: https://tinyman.gitbook.io/
- ⚛️ **React Docs**: https://react.dev/
- ⚡ **FastAPI Docs**: https://fastapi.tiangolo.com/

---

## Support

If you run into issues:

1. **Check the backend logs** – Look for error messages in Terminal 1
2. **Check browser console** – Open DevTools (F12) in your browser
3. **Check network requests** – Use the Network tab in DevTools
4. **Verify testnet account** – Use [AlgoExplorer Testnet](https://testnet.algoexplorer.io/)
5. **Read error messages carefully** – They usually indicate the problem clearly

---

**Ready to trade? 🚀 Let's go!**
