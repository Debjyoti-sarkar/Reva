# ════════════════════════════════════════════════════════════════════════════
# NexaVault – Complete Setup & Run Guide for Windows (PowerShell)
# ════════════════════════════════════════════════════════════════════════════
#
# This guide walks through:
# 1. Python virtual environment setup
# 2. Backend setup and contract deployment
# 3. Frontend setup
# 4. Running the complete system
#
# ════════════════════════════════════════════════════════════════════════════

Write-Host "NexaVault – Autonomous Algorand Trading Vault" -ForegroundColor Cyan -BackgroundColor Black
Write-Host "========================================================================================" -ForegroundColor Cyan

# ─────────────────────────────────────────────────────────────────────────────
# Step 1: Setup Python virtual environment for backend
# ─────────────────────────────────────────────────────────────────────────────

Write-Host "`n[1/5] Setting up Python virtual environment..." -ForegroundColor Yellow

if (-Not (Test-Path ".venv")) {
    Write-Host "  Creating virtual environment (.venv/)..."
    python -m venv .venv
} else {
    Write-Host "  Virtual environment already exists."
}

Write-Host "  Activating virtual environment..."
& ".\.venv\Scripts\Activate.ps1"

Write-Host "  Installing Python dependencies..." -ForegroundColor Green
pip install --upgrade pip
pip install -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install dependencies. Check your Python installation." -ForegroundColor Red
    exit 1
}
Write-Host "✅ Backend dependencies installed." -ForegroundColor Green

# ─────────────────────────────────────────────────────────────────────────────
# Step 2: Fund your testnet account (MANUAL)
# ─────────────────────────────────────────────────────────────────────────────

Write-Host "`n[2/5] Testnet account setup (MANUAL)" -ForegroundColor Yellow
Write-Host "  Before continuing, you MUST:"
Write-Host "    1. Generate a new Algorand testnet account (or use an existing one)"
Write-Host "    2. Fund it with test ALGO from the faucet"
Write-Host ""
Write-Host "  🔗 Fund your account here:"
Write-Host "    https://bank.testnet.algorand.network/"
Write-Host ""
Write-Host "  💡 To create a new account if you don't have one:"
Write-Host "    python -c ""from algosdk import account, mnemonic; pk, addr = account.generate_account(); print('Address:', addr); print('Mnemonic:', mnemonic.from_private_key(pk))"""
Write-Host ""
Write-Host "  ⚠️  IMPORTANT: Save your 25-word mnemonic securely!"
Write-Host "  ⚠️  NEVER share your mnemonic or private key!"
Write-Host ""

Read-Host "  Press ENTER when your account is funded with test ALGO (minimum 1 ALGO)"

# ─────────────────────────────────────────────────────────────────────────────
# Step 3: Create .env with your account key
# ─────────────────────────────────────────────────────────────────────────────

Write-Host "`n[3/5] Configuring .env file..." -ForegroundColor Yellow

$envExists = Test-Path ".env"

if ($envExists) {
    Write-Host "  .env file already exists. Preserving existing configuration..."
    Write-Host "  If you need to update your VAULT_MNEMONIC, edit .env manually."
} else {
    Write-Host "  Creating .env file..."
    Write-Host "  Please enter your 25-word mnemonic (from the account creation step above):"
    $mnemonic = Read-Host "  Mnemonic"
    
    # Create .env with the mnemonic
    $envContent = @"
ALGOD_URL=https://testnet-api.algonode.cloud
ALGOD_TOKEN=
APP_ID=0
VAULT_MNEMONIC=$mnemonic
BUY_THRESHOLD_USD=0.15
SELL_THRESHOLD_USD=0.22
TRADE_AMOUNT_MICROALGO=1000000
SLIPPAGE=0.01
AGENT_STRATEGY=rule
USE_MOCK_PRICE=false
TINYMAN_VALIDATOR_APP_ID=1002541853
USDC_ASSET_ID=10458941
ALLOWED_ORIGINS=http://localhost:3000
LOG_LEVEL=INFO
"@
    Set-Content -Path ".env" -Value $envContent
    Write-Host "✅ .env file created." -ForegroundColor Green
}

# ─────────────────────────────────────────────────────────────────────────────
# Step 4: Deploy the smart contract
# ─────────────────────────────────────────────────────────────────────────────

Write-Host "`n[4/5] Deploying smart contract to Testnet..." -ForegroundColor Yellow
Write-Host "  This will compile PyTeal → TEAL and deploy to Algorand Testnet."
Write-Host "  This requires your account to have at least 0.5 ALGO for fees."
Write-Host ""

python scripts/deploy_contract.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Smart contract deployment failed!" -ForegroundColor Red
    Write-Host "  Make sure:" -ForegroundColor Yellow
    Write-Host "    - Your account is funded with at least 1 ALGO" -ForegroundColor Yellow
    Write-Host "    - Your VAULT_MNEMONIC in .env is correct" -ForegroundColor Yellow
    Write-Host "    - You have internet access" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "⚠️  IMPORTANT: Copy the APP_ID from the output above!" -ForegroundColor Yellow
$appId = Read-Host "  Enter the APP_ID returned above"

# Update .env with APP_ID
$env:APP_ID = $appId
(Get-Content ".env") -replace "^APP_ID=.*", "APP_ID=$appId" | Set-Content ".env"
Write-Host "✅ APP_ID saved to .env" -ForegroundColor Green

# ─────────────────────────────────────────────────────────────────────────────
# Step 5: Setup and run frontend
# ─────────────────────────────────────────────────────────────────────────────

Write-Host "`n[5/5] Setting up frontend..." -ForegroundColor Yellow

$nodeInstalled = npm --version 2>$null
if (-Not $nodeInstalled) {
    Write-Host "❌ npm is not installed. Install Node.js from https://nodejs.org/" -ForegroundColor Red
    exit 1
}

Write-Host "  Installing frontend dependencies..."
cd frontend
npm install
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install frontend dependencies." -ForegroundColor Red
    exit 1
}
cd ..
Write-Host "✅ Frontend dependencies installed." -ForegroundColor Green

# ─────────────────────────────────────────────────────────────────────────────
# Ready to run!
# ─────────────────────────────────────────────────────────────────────────────

Write-Host "`n$('='*80)" -ForegroundColor Green
Write-Host "✅ SETUP COMPLETE!" -ForegroundColor Green
Write-Host "$('='*80)" -ForegroundColor Green

Write-Host "`n📋 NEXT STEPS – Run in separate terminals:" -ForegroundColor Cyan

Write-Host "`n🔵 Terminal 1 (Backend API):" -ForegroundColor Cyan
Write-Host "   cd C:\Users\DebSarkar\Desktop\lkj\Reva" -ForegroundColor Gray
Write-Host "   .\.venv\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host "   uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor Gray
Write-Host "   Expected output: Uvicorn running on http://0.0.0.0:8000" -ForegroundColor Gray

Write-Host "`n🟢 Terminal 2 (Frontend):" -ForegroundColor Cyan
Write-Host "   cd C:\Users\DebSarkar\Desktop\lkj\Reva\frontend" -ForegroundColor Gray
Write-Host "   npm start" -ForegroundColor Gray
Write-Host "   Expected output: Webpack compiled successfully and app opens at http://localhost:3000" -ForegroundColor Gray

Write-Host "`n🔴 Terminal 3 (Optional - Monitor logs):" -ForegroundColor Cyan
Write-Host "   Watch the backend terminal for trade logs and AI decisions" -ForegroundColor Gray

Write-Host "`n💡 USAGE:" -ForegroundColor Cyan
Write-Host "   1. Open http://localhost:3000 in your browser" -ForegroundColor Gray
Write-Host "   2. Click 'Connect Pera Wallet' and approve the connection" -ForegroundColor Gray
Write-Host "   3. Click '▶ Start Auto Trading' to begin autonomous trading" -ForegroundColor Gray
Write-Host "   4. Watch the dashboard for price updates and AI decisions" -ForegroundColor Gray
Write-Host "   5. Each trade will show buy/sell/hold decisions with confidence scores" -ForegroundColor Gray

Write-Host "`n🔗 API Endpoints:" -ForegroundColor Cyan
Write-Host "   GET  http://localhost:8000/                 - Health check" -ForegroundColor Gray
Write-Host "   GET  http://localhost:8000/price            - Current ALGO/USD price" -ForegroundColor Gray
Write-Host "   GET  http://localhost:8000/status           - Vault state & trade history" -ForegroundColor Gray
Write-Host "   POST http://localhost:8000/trade            - Trigger trade cycle" -ForegroundColor Gray
Write-Host "   POST http://localhost:8000/connect-wallet   - Register wallet address" -ForegroundColor Gray

Write-Host "`n⚠️  TESTNET FAUCETS (for more test ALGO/USDC):" -ForegroundColor Yellow
Write-Host "   ALGO Faucet:  https://bank.testnet.algorand.network/" -ForegroundColor Gray
Write-Host "   USDC Faucet:  https://testnet.algoexplorer.io/dispenser (search for USDC)" -ForegroundColor Gray

Write-Host "`n📚 DOCUMENTATION:" -ForegroundColor Cyan
Write-Host "   README.md       – Full project documentation" -ForegroundColor Gray
Write-Host "   .env.example    – All available environment variables" -ForegroundColor Gray
Write-Host "   backend/agent.py     – AI trading strategy logic" -ForegroundColor Gray
Write-Host "   contracts/trading_vault.py  – Smart contract code" -ForegroundColor Gray

Write-Host "`n$('='*80)" -ForegroundColor Cyan
Write-Host "Ready to trade! 🚀" -ForegroundColor Cyan
Write-Host "$('='*80)" -ForegroundColor Cyan
