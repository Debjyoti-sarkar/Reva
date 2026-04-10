# ⬡ NexaVault Algo Agent

**Autonomous Trading Vault on Algorand** — AI-driven buy/sell decisions, Pera Wallet integration, Tinyman DEX execution, and a PyTeal smart contract — all on Algorand **Testnet**.

```
  ┌─────────────┐     price      ┌──────────────┐    NoOp txn    ┌──────────────────┐
  │  Price Feed │ ─────────────► │  AI Agent    │ ─────────────► │  Vault Contract  │
  │ (CoinGecko) │                │ (Rule / ML)  │                │   (PyTeal)       │
  └─────────────┘                └──────┬───────┘                └──────────────────┘
                                        │ buy/sell
                                        ▼
                                 ┌──────────────┐
                                 │ Tinyman DEX  │
                                 │ ALGO ⇄ USDC  │
                                 └──────────────┘
                                        ▲
                                 ┌──────────────┐
                                 │  React UI    │
                                 │ Pera Wallet  │
                                 └──────────────┘
```

---

## 📑 Table of Contents

1. [Tech Stack](#tech-stack)
2. [Project Structure](#project-structure)
3. [Prerequisites](#prerequisites)
4. [Setup](#setup)
5. [Deploy the Smart Contract](#deploy-the-smart-contract)
6. [Run the Backend](#run-the-backend)
7. [Run the Frontend](#run-the-frontend)
8. [Connect Pera Wallet](#connect-pera-wallet)
9. [API Reference](#api-reference)
10. [AI Agent](#ai-agent)
11. [Environment Variables](#environment-variables)
12. [Testnet Resources](#testnet-resources)
13. [Production Checklist](#production-checklist)

---

## 🧩 Tech Stack

| Layer          | Technology                     |
|----------------|-------------------------------|
| Blockchain     | Algorand Testnet               |
| Smart Contract | PyTeal → TEAL v6               |
| Backend        | Python 3.11 + FastAPI          |
| Algorand SDK   | py-algorand-sdk (algosdk)      |
| DEX            | Tinyman V2 (tinyman-py-sdk)    |
| Price Feed     | CoinGecko REST API             |
| Frontend       | React 18                       |
| Wallet         | Pera Wallet (@perawallet/connect) |

---

## 📁 Project Structure

```
nexavault-algo-agent/
│
├── contracts/
│   ├── trading_vault.py      # PyTeal source — approval + clear programs
│   ├── approval.teal         # Compiled TEAL (auto-generated)
│   └── clear.teal            # Compiled TEAL (auto-generated)
│
├── backend/
│   ├── main.py               # FastAPI application + all endpoints
│   ├── agent.py              # AI trading agent (rule-based + ML hook)
│   ├── executor.py           # Algorand transaction builder & submitter
│   ├── tinyman_swap.py       # Tinyman V2 pool + swap logic
│   └── services/
│       └── price_feed.py     # ALGO/USD price (CoinGecko + mock fallback)
│
├── frontend/
│   ├── public/index.html
│   └── src/
│       ├── App.jsx           # React root — mounts PeraWalletProvider
│       ├── Dashboard.jsx     # Main trading UI
│       └── peraConnect.js    # Pera Wallet hook + context
│
├── config/
│   └── settings.py           # All environment-backed config values
│
├── scripts/
│   └── deploy_contract.py    # Compile PyTeal + deploy to Algorand Testnet
│
├── .env.example              # Copy → .env and fill in your values
├── requirements.txt
└── README.md
```

---

## ✅ Prerequisites

| Tool          | Version  | Install                              |
|---------------|----------|--------------------------------------|
| Python        | ≥ 3.11   | https://python.org                   |
| Node.js       | ≥ 18     | https://nodejs.org                   |
| npm           | ≥ 9      | bundled with Node.js                 |
| Pera Wallet   | iOS/Android | https://perawallet.app            |

You will also need a funded **Algorand Testnet** account.
Get free test ALGO from the [Testnet Dispenser](https://bank.testnet.algorand.network/).

---

## 🛠 Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-org/nexavault-algo-agent.git
cd nexavault-algo-agent
```

### 2. Create and activate a Python virtual environment

```bash
python -m venv .venv
source .venv/bin/activate          # macOS / Linux
# .venv\Scripts\activate           # Windows
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in at minimum:

```dotenv
VAULT_MNEMONIC=word1 word2 ... word25   # Your Testnet account mnemonic
APP_ID=0                                # Will be updated after deploy
```

> 💡 Generate a fresh Testnet account and fund it:
> ```bash
> python - <<'EOF'
> from algosdk import account, mnemonic
> pk, addr = account.generate_account()
> print("Address :", addr)
> print("Mnemonic:", mnemonic.from_private_key(pk))
> EOF
> ```
> Then visit https://bank.testnet.algorand.network/ and dispense to that address.

---

## 🚀 Deploy the Smart Contract

### Compile-only (no deployment)

```bash
python scripts/deploy_contract.py --compile-only
```

This writes `contracts/approval.teal` and `contracts/clear.teal`.

### Full deployment to Testnet

```bash
python scripts/deploy_contract.py
```

With custom thresholds (on-chain integers; $0.15 = 150000, $0.22 = 220000 in USD×1M format):

```bash
python scripts/deploy_contract.py --buy 150000000 --sell 220000000
```

**Sample output:**

```
🔧 Compiling PyTeal → TEAL ...
✅ TEAL files written to contracts/
🔧 Compiling TEAL via algod ...
✅ Bytecode compiled
🚀 Deploying from ABCDE...XYZ ...
💰 Account balance: 10.0000 ALGO
📤 Submitted deploy txn: ABCD1234...
═══════════════════════════════════════════════════════
✅ Contract deployed successfully!
   APP_ID  : 123456789
   TxID    : ABCD1234EFGH5678...
   Round   : 35012345
═══════════════════════════════════════════════════════

🔑 Add this to your .env or config/settings.py:
   APP_ID=123456789
```

**After deployment**, update your `.env`:

```dotenv
APP_ID=123456789
```

---

## ⚡ Run the Backend

```bash
# From the repo root, with .venv activated
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **Swagger UI** → http://localhost:8000/docs
- **ReDoc**       → http://localhost:8000/redoc
- **Health**      → http://localhost:8000/

### Using mock prices (no CoinGecko API needed)

```bash
USE_MOCK_PRICE=true uvicorn backend.main:app --reload
```

---

## 🖥 Run the Frontend

```bash
cd frontend
npm install
npm start
```

The React app opens at **http://localhost:3000**.

Create `frontend/.env` to point at your backend:

```dotenv
REACT_APP_API_URL=http://localhost:8000
REACT_APP_AUTO_TRADE_INTERVAL=60000
```

---

## 📱 Connect Pera Wallet

1. Install **Pera Wallet** on your phone ([iOS](https://apps.apple.com/app/pera-algo-wallet/id1459712385) / [Android](https://play.google.com/store/apps/details?id=com.algorand.android)).
2. Switch Pera Wallet to **Testnet**:
   - Settings → Developer Settings → Node Settings → Testnet
3. Fund your Testnet address:
   - https://bank.testnet.algorand.network/
4. Open the NexaVault UI at http://localhost:3000
5. Click **"Connect Pera Wallet"** — a QR code modal appears.
6. Scan the QR code with Pera Wallet.
7. Approve the connection — your address appears in the Dashboard.
8. Click **"Start Auto Trading"**.

> ⚠️ Always verify you are on **Testnet** in Pera Wallet before approving any transactions.

---

## 📡 API Reference

| Method | Endpoint          | Description                              |
|--------|-------------------|------------------------------------------|
| GET    | `/`               | Health check                             |
| POST   | `/connect-wallet` | Register wallet `{ address, network }`   |
| GET    | `/price`          | Current ALGO/USD price                   |
| POST   | `/trade`          | Run full AI → contract → DEX pipeline    |
| GET    | `/status`         | Last trade + vault on-chain state        |
| POST   | `/deposit`        | Record deposit `{ amount_microalgo }`    |
| POST   | `/withdraw`       | Record withdrawal `{ amount_microalgo }` |

### Example: trigger a trade

```bash
curl -X POST http://localhost:8000/trade \
  -H "Content-Type: application/json" \
  -d '{"wallet_address": "YOUR_ALGORAND_ADDRESS"}'
```

**Response:**

```json
{
  "action": "buy",
  "confidence": 0.87,
  "reason": "Price $0.142100 ≤ buy threshold $0.15. Triggering BUY.",
  "price_usd": 0.1421,
  "price_contract": 142100,
  "wallet": "YOUR_ALGORAND_ADDRESS",
  "timestamp": 1712345678.123,
  "contract_txn": {
    "txid": "ABCDEF123456...",
    "confirmed_round": 35012346,
    "op": "trade"
  },
  "swap": {
    "input_amount": 1000000,
    "output_amount": 142056,
    "price_impact": 0.0003,
    "transactions": ["base64_encoded_unsigned_txn..."]
  }
}
```

---

## 🤖 AI Agent

Located in `backend/agent.py`. Two strategies:

### Rule-Based (default)

Controlled by environment variables:

| Variable              | Default | Description                        |
|-----------------------|---------|------------------------------------|
| `BUY_THRESHOLD_USD`   | `0.15`  | Buy when price ≤ this              |
| `SELL_THRESHOLD_USD`  | `0.22`  | Sell when price ≥ this             |

Also implements a **momentum guard**: will not buy into a strongly falling market or sell into a strongly rising one.

### ML Strategy (plug-in hook)

Set `AGENT_STRATEGY=ml` and provide a pickled scikit-learn-compatible model at `MODEL_PATH`:

```python
# Train externally (e.g. with FinRL) then pickle:
import pickle
with open("models/nexavault_agent.pkl", "wb") as f:
    pickle.dump(trained_model, f)
```

Override `MLStrategy._build_features()` to match your model's input format.
Falls back to rule-based if the model file is missing.

---

## 🔐 Environment Variables

| Variable                    | Default                                    | Description                        |
|-----------------------------|--------------------------------------------|------------------------------------|
| `ALGOD_URL`                 | `https://testnet-api.algonode.cloud`       | Algorand node URL                  |
| `ALGOD_TOKEN`               | `` (empty)                                 | Node API token (Algonode = none)   |
| `APP_ID`                    | `0`                                        | Deployed vault app ID              |
| `VAULT_MNEMONIC`            | —                                          | 25-word account mnemonic           |
| `VAULT_PRIVATE_KEY`         | —                                          | Base64 private key (alt to mnemonic) |
| `BUY_THRESHOLD_USD`         | `0.15`                                     | Rule agent buy threshold           |
| `SELL_THRESHOLD_USD`        | `0.22`                                     | Rule agent sell threshold          |
| `TRADE_AMOUNT_MICROALGO`    | `1000000` (1 ALGO)                         | Trade size per cycle               |
| `SLIPPAGE`                  | `0.01` (1%)                                | Tinyman slippage tolerance         |
| `AGENT_STRATEGY`            | `rule`                                     | `rule` or `ml`                     |
| `MODEL_PATH`                | `models/nexavault_agent.pkl`               | Path to pickled ML model           |
| `USE_MOCK_PRICE`            | `false`                                    | Use mock price instead of API      |
| `TINYMAN_VALIDATOR_APP_ID`  | `1002541853`                               | Tinyman V2 Testnet app ID          |
| `USDC_ASSET_ID`             | `10458941`                                 | Testnet USDC asset ID              |
| `ALLOWED_ORIGINS`           | `http://localhost:3000`                    | CORS allowed origins (comma-sep)   |
| `LOG_LEVEL`                 | `INFO`                                     | Python logging level               |

---

## 🌐 Testnet Resources

| Resource              | URL                                                        |
|-----------------------|------------------------------------------------------------|
| Algorand Testnet Node | https://testnet-api.algonode.cloud                         |
| Testnet Dispenser     | https://bank.testnet.algorand.network/                     |
| Testnet Explorer      | https://testnet.algoexplorer.io/                           |
| Tinyman Testnet       | https://testnet.tinyman.org/                               |
| Pera Wallet           | https://perawallet.app/                                    |
| Algo Dev Docs         | https://developer.algorand.org/                            |

---

## 🏭 Production Checklist

Before deploying to Algorand **Mainnet**:

- [ ] Replace `VAULT_MNEMONIC` with an HSM or KMS-backed key
- [ ] Set `ALGOD_URL` to a dedicated Mainnet node (e.g. [Nodely](https://nodely.io))
- [ ] Update `APP_ID` to the Mainnet-deployed contract
- [ ] Update `USDC_ASSET_ID` to Mainnet USDC (`31566704`)
- [ ] Update `TINYMAN_VALIDATOR_APP_ID` to Mainnet value (`1002541853` → check Tinyman docs)
- [ ] Increase `WAIT_ROUNDS` for production safety
- [ ] Swap in-memory `_state` dict for Redis / a database
- [ ] Add authentication to `/trade`, `/deposit`, `/withdraw` endpoints
- [ ] Set `ALLOWED_ORIGINS` to your production domain only
- [ ] Enable HTTPS (use a reverse proxy: nginx, Caddy, etc.)
- [ ] Add rate limiting to the FastAPI app
- [ ] Set up monitoring (Prometheus + Grafana or similar)
- [ ] Audit the smart contract with a third-party security firm

---

## 📜 License

MIT — see [LICENSE](LICENSE)

---

> ⚠️ **Disclaimer**: This project is for educational and demonstration purposes only.
> Autonomous trading carries significant financial risk. Never use real funds without
> extensive testing, security audits, and regulatory review. Always comply with
> applicable financial regulations in your jurisdiction.
