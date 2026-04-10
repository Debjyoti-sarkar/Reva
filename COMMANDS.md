# 🚀 NexaVault – Master Commands Cheat Sheet

## ⚡ Running in 3 Steps

### Step 1: Deploy Smart Contract (ONE TIME ONLY)
```powershell
cd C:\Users\DebSarkar\Desktop\lkj\Reva
.\.venv\Scripts\Activate.ps1  # If not already activated
python scripts/deploy_contract.py
# 👀 Copy the APP_ID from output and update .env
```

### Step 2: Start Backend (Terminal 1)
```powershell
cd C:\Users\DebSarkar\Desktop\lkj\Reva
.\.venv\Scripts\Activate.ps1
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
# ✅ Ready when you see: "Uvicorn running on http://0.0.0.0:8000"
```

### Step 3: Start Frontend (Terminal 2)
```powershell
cd C:\Users\DebSarkar\Desktop\lkj\Reva\frontend
npm start
# ✅ Ready when browser opens to http://localhost:3000
```

---

## 🔧 All Commands Reference

### Python Venv
```powershell
# Create virtual environment
python -m venv .venv

# Activate (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Deactivate
deactivate

# Upgrade pip
python -m pip install --upgrade pip
```

### Backend Setup
```powershell
# Install dependencies
pip install -r requirements.txt

# Test imports
python -c "from backend.main import app; print('OK')"

# Run with auto-reload (development)
uvicorn backend.main:app --reload

# Run without auto-reload (production)
uvicorn backend.main:app

# Run on different port
uvicorn backend.main:app --port 8001

# View Swagger docs (while running)
# Open: http://localhost:8000/docs
```

### Smart Contract
```powershell
# Compile only
python scripts/deploy_contract.py --compile-only

# Deploy with custom thresholds
python scripts/deploy_contract.py --buy 150000000 --sell 220000000

# View TEAL output
cat contracts/approval.teal
cat contracts/clear.teal
```

### Frontend Setup
```powershell
cd frontend

# Install dependencies
npm install

# Start development server
npm start

# Build for production
npm run build

# Run tests
npm test
```

### Testing API
```powershell
# Health check
curl http://localhost:8000/

# Get price
curl http://localhost:8000/price

# Get status
curl http://localhost:8000/status

# Trigger trade
curl -X POST http://localhost:8000/trade `
  -H "Content-Type: application/json" `
  -d '{"wallet_address":"XXXXXX...XXXXXX"}'

# View API docs (interactive)
# Open while backend running: http://localhost:8000/docs
```

### Debugging
```powershell
# Check Python version
python --version

# Check Node version
node --version
npm --version

# Find process on port 8000
netstat -ano | findstr :8000

# Kill process on port 8000
taskkill /PID {PID} /F

# Check .env file
cat .env

# Check git status
git status

# View backend logs
# Watch Terminal 1 where uvicorn is running

# View frontend logs
# Check browser console (F12 in browser)
```

---

## 📝 Configuration Files

### Main .env File
```env
# Location: C:\Users\DebSarkar\Desktop\lkj\Reva\.env

# Algorand Node
ALGOD_URL=https://testnet-api.algonode.cloud
ALGOD_TOKEN=

# Smart Contract (set after deploying)
APP_ID=0  # ← UPDATE THIS after running deploy_contract.py

# Your TestNet Account Signing Key (KEEP SECRET!)
VAULT_MNEMONIC=your twenty five word seed phrase here

# Trading Thresholds
BUY_THRESHOLD_USD=0.15
SELL_THRESHOLD_USD=0.22
TRADE_AMOUNT_MICROALGO=1000000

# AI & Price Settings
AGENT_STRATEGY=rule
USE_MOCK_PRICE=false

# Logging
LOG_LEVEL=INFO
```

### Frontend .env File
```env
# Location: C:\Users\DebSarkar\Desktop\lkj\Reva\frontend\.env

REACT_APP_API_URL=http://localhost:8000
REACT_APP_AUTO_TRADE_INTERVAL=60000
```

---

## 🔌 Port Reference

| Port | Service | URL |
|------|---------|-----|
| 8000 | Backend API | http://localhost:8000 |
| 8000/docs | API Swagger | http://localhost:8000/docs |
| 3000 | Frontend | http://localhost:3000 |

---

## 📊 File Locations

```
Project Root: C:\Users\DebSarkar\Desktop\lkj\Reva

Key Files:
├── Main Backend
│   ├── backend/main.py                 (FastAPI app)
│   ├── backend/agent.py                 (AI logic)
│   ├── backend/executor.py              (Contracts)
│   └── backend/tinyman_swap.py          (DEX swaps)
│
├── Smart Contract
│   ├── contracts/trading_vault.py       (PyTeal)
│   └── scripts/deploy_contract.py       (Deployer)
│
├── Frontend
│   ├── frontend/src/App.jsx             (React root)
│   ├── frontend/src/Dashboard.jsx       (UI)
│   └── frontend/src/peraConnect.js      (Wallet)
│
├── Config
│   ├── .env                             (YOUR SECRETS)
│   ├── .env.example                     (Template)
│   └── config/settings.py               (Loader)
│
└── Documentation
    ├── IMPLEMENTATION_COMPLETE.md       (What was done)
    ├── SETUP_GUIDE.md                   (Full guide)
    ├── QUICK_REF.md                     (Quick ref)
    └── SETUP.ps1                        (Auto setup)
```

---

## 🧪 Test Scenarios

### Scenario 1: Check Backend Health
```powershell
# In new terminal
curl http://localhost:8000/
# Expected: {"status":"ok",...}
```

### Scenario 2: Manual Trade (via API)
```powershell
$wallet = "YOUR_WALLET_ADDRESS"
curl -X POST http://localhost:8000/trade `
  -H "Content-Type: application/json" `
  -d "{`"wallet_address`":`"$wallet`"}"
```

### Scenario 3: Price Feed Test
```powershell
curl http://localhost:8000/price
# Expected: {"price_usd":0.175,"price_contract":175000,"source":"coingecko"}

# OR with mock (if API down)
# Edit .env: USE_MOCK_PRICE=true
# Restart backend
```

### Scenario 4: Full UI Test
1. Open http://localhost:3000
2. Connect Pera Wallet (scan QR code with phone)
3. Wait for price to load
4. Click "Start Auto Trading"
5. Watch for trades to execute
6. View trade history in dashboard

---

## 🔐 Security Checklist

```powershell
# NEVER COMMIT THESE:
.gitignore should contain:
  .env
  .venv/
  node_modules/
  __pycache__/

# NEVER SHARE:
  - Your VAULT_MNEMONIC
  - Your VAULT_PRIVATE_KEY
  - Your APP_ID (not secret, but keep safe)

# VERIFY BEFORE DEPLOYMENT:
  - Testnet only (not mainnet)
  - Mock prices disabled in production
  - Proper error handling
  - No hardcoded secrets
```

---

## 🆘 Emergency Fixes

### "Address already in use: 0.0.0.0:8000"
```powershell
# Option A: Kill the process
netstat -ano | findstr :8000
taskkill /PID {PID} /F

# Option B: Use different port
uvicorn backend.main:app --port 8001
```

### "Failed to import backend.main"
```powershell
# Make sure venv is activated
.\.venv\Scripts\Activate.ps1

# Reinstall dependencies
pip install -r requirements.txt
```

### "npm: command not found"
```powershell
# Install Node.js from: https://nodejs.org/
# Then restart PowerShell
node --version
npm --version
```

### "Contract deployment failed"
```powershell
# 1. Check account funding
# 2. Verify VAULT_MNEMONIC in .env
# 3. Check ALGOD_URL is accessible
# 4. Try again

python scripts/deploy_contract.py
```

### "Price is always 0"
```powershell
# Set mock price in .env
USE_MOCK_PRICE=true

# Restart backend
# CTRL+C to stop, then rerun uvicorn
```

---

## 📊 Performance Tuning

### Reduce Trade Frequency
```env
# In frontend/.env
REACT_APP_AUTO_TRADE_INTERVAL=120000  # 2 minutes instead of 1
```

### Increase Trade Size
```env
# In .env
TRADE_AMOUNT_MICROALGO=5000000  # 5 ALGO instead of 1
```

### Change Thresholds
```env
# Buy much lower
BUY_THRESHOLD_USD=0.10

# Sell much higher
SELL_THRESHOLD_USD=0.30
```

### Use Larger Slippage
```env
# Allow 2% instead of 1%
SLIPPAGE=0.02
```

---

## 📚 Learning Resources

| Topic | Link |
|-------|------|
| Algorand | https://developer.algorand.org/ |
| PyTeal | https://pyteal.readthedocs.io/ |
| algosdk | https://py-algorand-sdk.readthedocs.io/ |
| FastAPI | https://fastapi.tiangolo.com/ |
| React | https://react.dev/ |
| Pera Wallet | https://github.com/perawallet/connect |
| Tinyman | https://tinyman.gitbook.io/ |

---

## 🎯 Quick Status Check

```powershell
# All in one terminal
echo "=== Python ==="
python --version

echo "`n=== Node ==="
node --version
npm --version

echo "`n=== Backend Health ==="
curl -s http://localhost:8000/ | ConvertFrom-Json | Select-Object status

echo "`n=== Frontend Health ==="
Start-Process http://localhost:3000

echo "`n=== Environment ==="
cat .env | Select-String "APP_ID|VAULT_MNEMONIC|BUY_THRESHOLD"
```

---

## ⏱️ Typical First Run Timeline

```
T+0:00  Run .\SETUP.ps1
T+2:00  Activate venv
T+3:00  Install dependencies
T+5:00  Prompt for mnemonic
T+6:00  Fund account (manual – follow link)
T+9:00  Deploy contract (wait for testnet)
T+12:00 Install frontend dependencies
T+13:00 Ready for manual run
T+14:00 Start backend (Terminal 1)
T+15:00 Start frontend (Terminal 2)
T+16:00 Open http://localhost:3000
T+17:00 Connect Pera Wallet
T+18:00 Click "Start Auto Trading"
T+20:00 First trade executes!
```

---

## ✅ Pre-Launch Checklist

- [ ] Python 3.9+ installed
- [ ] Node.js 16+ installed
- [ ] Testnet account created & funded (2+ ALGO)
- [ ] VAULT_MNEMONIC saved securely
- [ ] .env file created with mnemonic
- [ ] backend/requirements.txt installed
- [ ] Smart contract deployed (APP_ID obtained)
- [ ] APP_ID updated in .env
- [ ] frontend/package.json dependencies installed
- [ ] Backend starts without errors
- [ ] Frontend starts and opens browser
- [ ] Pera Wallet app installed on phone
- [ ] Pera Wallet set to Testnet mode

---

**Everything Ready? Run This:**

```powershell
cd C:\Users\DebSarkar\Desktop\lkj\Reva

# Terminal 1
.\.venv\Scripts\Activate.ps1
uvicorn backend.main:app --reload

# Terminal 2 (new window)
cd frontend
npm start

# Terminal 3 (optional)
# Watch backend logs

# Browser: http://localhost:3000
# Enjoy! 🎉
```

---

**Questions? See:**
- IMPLEMENTATION_COMPLETE.md (what was built)
- SETUP_GUIDE.md (detailed instructions)
- QUICK_REF.md (quick answers)

**Ready to trade? GO! 🚀**
