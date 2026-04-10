# NexaVault – Quick Reference Guide

## 🚀 Quick Start (5 Minutes)

### Prerequisites Checklist
- [ ] Python 3.9+ installed (`python --version`)
- [ ] Node.js 16+ installed (`node --version`)
- [ ] Algebra testnet account funded with 2+ ALGO
- [ ] VAULT_MNEMONIC in `.env` file

### Step-by-Step Quick Start

```powershell
# 1. Navigate to project
cd C:\Users\DebSarkar\Desktop\lkj\Reva

# 2. Run setup wizard
.\SETUP.ps1
# Follow the prompts to:
# - Setup Python virtual environment
# - Fund your testnet account
# - Deploy smart contract
# - Install frontend dependencies

# 3. Start Backend (Terminal 1)
.\.venv\Scripts\Activate.ps1
uvicorn backend.main:app --reload --port 8000

# 4. Start Frontend (Terminal 2)
cd frontend
npm start
# Opens http://localhost:3000 automatically

# 5. Use in browser
# - Connect Pera Wallet
# - Click "Start Auto Trading"
# - Watch trades execute in real-time!
```

---

## 📊 System Commands

### Backend Only (API for testing)
```powershell
cd C:\Users\DebSarkar\Desktop\lkj\Reva
.\.venv\Scripts\Activate.ps1
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Only
```powershell
cd C:\Users\DebSarkar\Desktop\lkj\Reva\frontend
npm start
```

### Deploy Contract Only
```powershell
cd C:\Users\DebSarkar\Desktop\lkj\Reva
.\.venv\Scripts\Activate.ps1
python scripts/deploy_contract.py
```

### Check Backend Health
```powershell
curl http://localhost:8000/
# Returns: {"status":"ok","service":"nexavault-algo-agent",...}
```

### Test Price Feed
```powershell
curl http://localhost:8000/price
# Returns: {"price_usd":0.175,"price_contract":175000,"source":"coingecko"}
```

### Trigger Manual Trade
```powershell
curl -X POST http://localhost:8000/trade `
  -H "Content-Type: application/json" `
  -d '{"wallet_address":"XXXXXX...XXXXXX"}'
```

---

## 🔧 Configuration Quick Reference

### .env File Template
```env
# Essential
ALGOD_URL=https://testnet-api.algonode.cloud
VAULT_MNEMONIC=word1 word2 word3 ... word25
APP_ID=123456789

# Trading Thresholds
BUY_THRESHOLD_USD=0.15
SELL_THRESHOLD_USD=0.22

# Price Feed
USE_MOCK_PRICE=false

# AI Strategy
AGENT_STRATEGY=rule
```

### Environment Variables
| Variable | Value | Description |
|----------|-------|-------------|
| `VAULT_MNEMONIC` | 25 words | Your testnet account seed |
| `APP_ID` | Integer | Smart contract ID (after deploy) |
| `BUY_THRESHOLD_USD` | Float | Buy when price ≤ this |
| `SELL_THRESHOLD_USD` | Float | Sell when price ≥ this |
| `AGENT_STRATEGY` | rule/ml | Which trading strategy |
| `USE_MOCK_PRICE` | true/false | Use mock or CoinGecko for price |
| `LOG_LEVEL` | DEBUG/INFO/WARNING/ERROR | How verbose the logs are |

---

## 🐛 Troubleshooting Quick Fixes

| Problem | Solution |
|---------|----------|
| ModuleNotFoundError | `.\.venv\Scripts\Activate.ps1` then `pip install -r requirements.txt` |
| Address already in use | Change port: `uvicorn backend.main:app --port 8001` |
| Insufficient balance | Fund account: https://bank.testnet.algorand.network/ |
| Pera Wallet error | Reinstall Pera app, ensure Testnet mode, check network |
| Price is 0 | Set `USE_MOCK_PRICE=true` in `.env` |
| Contract deployment fails | 1) Fund account 2) Check VAULT_MNEMONIC 3) Retry |
| npm: command not found | Install Node.js from nodejs.org |

---

## 📡 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Health check |
| `/price` | GET | Current ALGO/USD price |
| `/trade` | POST | Execute trade cycle |
| `/status` | GET | Vault state & history |
| `/connect-wallet` | POST | Register wallet |
| `/deposit` | POST | Record deposit |
| `/withdraw` | POST | Record withdrawal |

**All endpoints documented in FastAPI Swagger:**
- Visit: http://localhost:8000/docs
- Try requests directly in browser

---

## 💡 Common Tasks

### Check if Backend is Running
```powershell
curl http://localhost:8000/ -ErrorAction SilentlyContinue
```

### View Backend Logs
Watch Terminal 1 where uvicorn is running

### View Frontend Logs
Watch Terminal 2 / browser console (F12)

### Find Your Smart Contract
```
https://testnet.algoexplorer.io/application/{APP_ID}
```

### Fund Your Testnet Account
```
https://bank.testnet.algorand.network/
```

### Generate New Testnet Account
```powershell
python -c "from algosdk import account, mnemonic; pk, addr = account.generate_account(); print(f'Address: {addr}'); print(f'Mnemonic: {mnemonic.from_private_key(pk)}')"
```

### Kill Process on Port 8000
```powershell
netstat -ano | findstr :8000
taskkill /PID {PID} /F
```

---

## 📚 Key Files Overview

```
Reva/
├── backend/                    # FastAPI backend
│   ├── main.py                # All API endpoints
│   ├── agent.py               # AI trading logic
│   ├── executor.py            # Execute transactions
│   ├── tinyman_swap.py         # Swap integration
│   └── services/
│       └── price_feed.py       # CoinGecko price fetch
├── contracts/
│   └── trading_vault.py        # Smart contract (PyTeal)
├── scripts/
│   └── deploy_contract.py      # Deployment script
├── frontend/                   # React frontend
│   ├── package.json            # Node dependencies
│   ├── public/
│   │   └── index.html          # HTML template
│   └── src/
│       ├── App.jsx             # Root component
│       ├── Dashboard.jsx        # Main UI
│       └── peraConnect.js       # Wallet integration
├── config/
│   └── settings.py             # Configuration loader
├── .env                        # YOUR SECRET CONFIG (don't commit!)
├── .env.example                # Template for .env
├── requirements.txt            # Python dependencies
└── SETUP_GUIDE.md             # Full setup documentation
```

---

## 🔐 Security Checklist

- [ ] Never commit `.env` to git (add to `.gitignore`)
- [ ] Never share your VAULT_MNEMONIC or VAULT_PRIVATE_KEY
- [ ] Use testnet accounts for development only
- [ ] In production, use proper secret management (AWS Secrets, Vault)
- [ ] Keep the APP_ID safe but it's not secret
- [ ] Rotate keys regularly in production

---

## 📞 Support Resources

- 📖 Full Setup Guide: `SETUP_GUIDE.md`
- 🏗️ Architecture: See diagrams in README.md
- 🤖 AI Logic: Read comments in `backend/agent.py`
- 📜 Smart Contract: Read comments in `contracts/trading_vault.py`
- 🔗 Algorand Docs: https://developer.algorand.org/
- 💬 Algorand Discord: https://discord.gg/algorand

---

## ⏱️ Typical Session Timeline

```
T+0:00   Start backend                    → uvicorn log output
T+0:05   Start frontend                   → React opens at localhost:3000
T+0:10   Connect Pera Wallet              → Dashboard shows wallet
T+0:15   Fetch price                      → Shows "$0.175 ALGO/USD"
T+0:20   Click "Start Auto Trading"        → Begins 60s cycle
T+0:25   First trade cycle                → Buy/Sell/Hold decision (check logs!)
T+1:25   Second trade cycle               → Another decision + actual transaction
T+2:25   View trade history               → See all executed trades
T+5:00   Manual trigger                   → Execute trade immediately
T+X:00   Stop auto trading                → Click stop, check vault state
```

---

**Ready? Run `.\.SETUP.ps1` and let's go! 🚀**
