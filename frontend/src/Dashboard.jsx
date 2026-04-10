/**
 * NexaVault – Trading Dashboard
 * ================================
 * Main UI for monitoring the autonomous vault and triggering trades.
 *
 * Shows:
 *  - Connected wallet address
 *  - Current ALGO/USD price
 *  - AI agent decision (buy / sell / hold)
 *  - Vault on-chain state
 *  - Trade history (in-memory this session)
 *  - Controls: Start Auto Trading, Stop, Manual Trigger
 */

import { useState, useEffect, useRef, useCallback } from "react";
import { usePeraWallet } from "./peraConnect";

const API_BASE = process.env.REACT_APP_API_URL ?? "http://localhost:8000";

// Auto-trade interval in milliseconds (default 60 s)
const AUTO_TRADE_INTERVAL_MS = Number(
  process.env.REACT_APP_AUTO_TRADE_INTERVAL ?? "60000"
);

// ── Helpers ──────────────────────────────────────────────────────────────────

const formatAddress = (addr) =>
  addr ? `${addr.slice(0, 6)}…${addr.slice(-4)}` : "—";

const formatUSD = (n) =>
  n != null ? `$${Number(n).toFixed(6)}` : "—";

const actionColor = (action) => {
  if (action === "buy")  return "#22c55e";   // green
  if (action === "sell") return "#ef4444";   // red
  return "#94a3b8";                           // slate (hold)
};

const actionLabel = (action) => {
  if (action === "buy")  return "🟢 BUY";
  if (action === "sell") return "🔴 SELL";
  return "⚪ HOLD";
};


// ─────────────────────────────────────────────
// Dashboard Component
// ─────────────────────────────────────────────

export default function Dashboard() {
  const { address, isConnected, isConnecting, connect, disconnect, error: walletError } =
    usePeraWallet();

  const [price, setPrice]           = useState(null);
  const [lastTrade, setLastTrade]   = useState(null);
  const [vaultState, setVaultState] = useState(null);
  const [tradeHistory, setHistory]  = useState([]);
  const [isTrading, setIsTrading]   = useState(false);
  const [isRunning, setIsRunning]   = useState(false);
  const [apiError, setApiError]     = useState(null);
  const [statusMsg, setStatus]      = useState("Ready");

  const autoTradeTimer = useRef(null);

  // ── Register wallet with backend on connect ─────────────────────────────
  useEffect(() => {
    if (!isConnected || !address) return;
    fetch(`${API_BASE}/connect-wallet`, {
      method : "POST",
      headers: { "Content-Type": "application/json" },
      body   : JSON.stringify({ address, network: "testnet" }),
    })
      .then((r) => r.json())
      .then(() => setStatus(`Wallet registered: ${formatAddress(address)}`))
      .catch((e) => setApiError(`Backend register error: ${e.message}`));
  }, [isConnected, address]);

  // ── Fetch price every 30 seconds ─────────────────────────────────────────
  const fetchPrice = useCallback(async () => {
    try {
      const r = await fetch(`${API_BASE}/price`);
      const d = await r.json();
      setPrice(d);
    } catch {
      // Non-fatal – keep showing last price
    }
  }, []);

  useEffect(() => {
    fetchPrice();
    const t = setInterval(fetchPrice, 30_000);
    return () => clearInterval(t);
  }, [fetchPrice]);

  // ── Fetch status ──────────────────────────────────────────────────────────
  const fetchStatus = useCallback(async () => {
    try {
      const r = await fetch(`${API_BASE}/status`);
      const d = await r.json();
      setLastTrade(d.last_trade);
      setVaultState(d.vault_state);
    } catch {
      /* non-fatal */
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    const t = setInterval(fetchStatus, 15_000);
    return () => clearInterval(t);
  }, [fetchStatus]);

  // ── Run one trade cycle ───────────────────────────────────────────────────
  const runTrade = useCallback(async () => {
    if (isTrading || !isConnected) return;
    setIsTrading(true);
    setApiError(null);
    setStatus("⚙️  Running AI trade cycle...");

    try {
      const r = await fetch(`${API_BASE}/trade`, {
        method : "POST",
        headers: { "Content-Type": "application/json" },
        body   : JSON.stringify({ wallet_address: address }),
      });

      if (!r.ok) {
        const err = await r.json();
        throw new Error(err.detail ?? r.statusText);
      }

      const d = await r.json();
      setLastTrade(d);
      setHistory((prev) => [d, ...prev].slice(0, 20));  // keep last 20
      setStatus(`✅ Trade cycle complete – ${actionLabel(d.action)}`);
    } catch (e) {
      setApiError(e.message);
      setStatus("❌ Trade error – see error panel");
    } finally {
      setIsTrading(false);
    }
  }, [isTrading, isConnected, address]);

  // ── Auto trading loop ─────────────────────────────────────────────────────
  const startAutoTrading = useCallback(() => {
    if (isRunning) return;
    setIsRunning(true);
    setStatus("🤖 Auto trading started");
    runTrade();   // run immediately
    autoTradeTimer.current = setInterval(runTrade, AUTO_TRADE_INTERVAL_MS);
  }, [isRunning, runTrade]);

  const stopAutoTrading = useCallback(() => {
    clearInterval(autoTradeTimer.current);
    setIsRunning(false);
    setStatus("⏹ Auto trading stopped");
  }, []);

  useEffect(() => () => clearInterval(autoTradeTimer.current), []);

  // ──────────────────────────────────────────────────────────────────────────
  // Render
  // ──────────────────────────────────────────────────────────────────────────

  return (
    <div style={styles.page}>
      {/* ── Header ──────────────────────────────────────────────────────── */}
      <header style={styles.header}>
        <div style={styles.logo}>⬡ NexaVault</div>
        <div style={styles.network}>Algorand Testnet</div>
      </header>

      {/* ── Wallet Card ──────────────────────────────────────────────────── */}
      <Card title="🔗 Wallet">
        {isConnected ? (
          <div style={styles.row}>
            <span style={styles.badge}>Connected</span>
            <code style={styles.address}>{address}</code>
            <button style={styles.btnSecondary} onClick={disconnect}>
              Disconnect
            </button>
          </div>
        ) : (
          <button style={styles.btnPrimary} onClick={connect} disabled={isConnecting}>
            {isConnecting ? "Connecting…" : "Connect Pera Wallet"}
          </button>
        )}
        {walletError && <p style={styles.error}>{walletError}</p>}
      </Card>

      {/* ── Price Card ────────────────────────────────────────────────────── */}
      <Card title="💰 ALGO / USD Price">
        <BigNum value={formatUSD(price?.price_usd)} />
        {price && (
          <sub style={styles.sub}>
            Source: {price.source} · Contract: {price.price_contract}
          </sub>
        )}
      </Card>

      {/* ── Trading Controls ──────────────────────────────────────────────── */}
      <Card title="🤖 Autonomous Trading">
        <p style={styles.statusMsg}>{statusMsg}</p>
        <div style={styles.btnRow}>
          {!isRunning ? (
            <button
              style={{ ...styles.btnPrimary, background: "#22c55e" }}
              onClick={startAutoTrading}
              disabled={!isConnected || isTrading}
            >
              ▶ Start Auto Trading
            </button>
          ) : (
            <button
              style={{ ...styles.btnPrimary, background: "#ef4444" }}
              onClick={stopAutoTrading}
            >
              ⏹ Stop Auto Trading
            </button>
          )}
          <button
            style={styles.btnSecondary}
            onClick={runTrade}
            disabled={!isConnected || isTrading || isRunning}
          >
            {isTrading ? "Running…" : "⚡ Manual Trigger"}
          </button>
        </div>
      </Card>

      {/* ── Last Trade ────────────────────────────────────────────────────── */}
      {lastTrade && (
        <Card title="📊 Last Trade">
          <div style={{ ...styles.actionBadge, background: actionColor(lastTrade.action) }}>
            {actionLabel(lastTrade.action)}
          </div>
          <dl style={styles.dl}>
            <dt>Price</dt>      <dd>{formatUSD(lastTrade.price_usd)}</dd>
            <dt>Confidence</dt> <dd>{(lastTrade.confidence * 100).toFixed(1)}%</dd>
            <dt>Reason</dt>     <dd>{lastTrade.reason}</dd>
            {lastTrade.contract_txn?.txid && (
              <>
                <dt>TxID</dt>
                <dd>
                  <a
                    href={`https://testnet.algoexplorer.io/tx/${lastTrade.contract_txn.txid}`}
                    target="_blank"
                    rel="noreferrer"
                    style={styles.link}
                  >
                    {lastTrade.contract_txn.txid.slice(0, 16)}…
                  </a>
                </dd>
              </>
            )}
          </dl>
        </Card>
      )}

      {/* ── Vault State ────────────────────────────────────────────────────── */}
      {vaultState && !vaultState.error && (
        <Card title="🏦 Vault Contract State">
          <dl style={styles.dl}>
            {Object.entries(vaultState).map(([k, v]) => (
              <span key={k}><dt>{k}</dt><dd>{String(v)}</dd></span>
            ))}
          </dl>
        </Card>
      )}

      {/* ── Trade History ────────────────────────────────────────────────── */}
      {tradeHistory.length > 0 && (
        <Card title="📋 Trade History (this session)">
          <table style={styles.table}>
            <thead>
              <tr>
                <th>Time</th><th>Action</th><th>Price (USD)</th><th>Confidence</th>
              </tr>
            </thead>
            <tbody>
              {tradeHistory.map((t, i) => (
                <tr key={i}>
                  <td>{new Date(t.timestamp * 1000).toLocaleTimeString()}</td>
                  <td style={{ color: actionColor(t.action), fontWeight: 700 }}>
                    {t.action?.toUpperCase()}
                  </td>
                  <td>{formatUSD(t.price_usd)}</td>
                  <td>{(t.confidence * 100).toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      {/* ── API Error ────────────────────────────────────────────────────── */}
      {apiError && (
        <Card title="⚠️ Error">
          <p style={styles.error}>{apiError}</p>
          <button style={styles.btnSecondary} onClick={() => setApiError(null)}>
            Dismiss
          </button>
        </Card>
      )}
    </div>
  );
}


// ── Sub-components ────────────────────────────────────────────────────────────

function Card({ title, children }) {
  return (
    <div style={styles.card}>
      <h3 style={styles.cardTitle}>{title}</h3>
      {children}
    </div>
  );
}

function BigNum({ value }) {
  return <div style={styles.bigNum}>{value}</div>;
}


// ── Styles ────────────────────────────────────────────────────────────────────

const styles = {
  page        : { maxWidth: 720, margin: "0 auto", padding: "24px 16px", fontFamily: "system-ui, sans-serif", color: "#e2e8f0", background: "#0f172a", minHeight: "100vh" },
  header      : { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 28 },
  logo        : { fontSize: 26, fontWeight: 800, color: "#38bdf8", letterSpacing: -1 },
  network     : { fontSize: 12, color: "#64748b", background: "#1e293b", padding: "4px 10px", borderRadius: 12 },
  card        : { background: "#1e293b", borderRadius: 14, padding: 20, marginBottom: 18, border: "1px solid #334155" },
  cardTitle   : { margin: "0 0 14px", fontSize: 14, fontWeight: 700, color: "#94a3b8", textTransform: "uppercase", letterSpacing: 1 },
  row         : { display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" },
  badge       : { background: "#22c55e", color: "#fff", fontSize: 11, padding: "3px 8px", borderRadius: 6, fontWeight: 700 },
  address     : { background: "#0f172a", padding: "4px 10px", borderRadius: 6, fontSize: 13, color: "#38bdf8", flexGrow: 1, wordBreak: "break-all" },
  bigNum      : { fontSize: 42, fontWeight: 800, color: "#38bdf8", letterSpacing: -2 },
  sub         : { color: "#64748b", fontSize: 11, display: "block", marginTop: 6 },
  statusMsg   : { color: "#94a3b8", fontSize: 13, marginBottom: 14 },
  btnRow      : { display: "flex", gap: 10, flexWrap: "wrap" },
  btnPrimary  : { background: "#0ea5e9", color: "#fff", border: "none", borderRadius: 8, padding: "10px 22px", fontWeight: 700, cursor: "pointer", fontSize: 14 },
  btnSecondary: { background: "#334155", color: "#e2e8f0", border: "none", borderRadius: 8, padding: "10px 18px", fontWeight: 600, cursor: "pointer", fontSize: 14 },
  actionBadge : { display: "inline-block", color: "#fff", padding: "6px 14px", borderRadius: 8, fontWeight: 800, fontSize: 18, marginBottom: 14 },
  dl          : { display: "grid", gridTemplateColumns: "140px 1fr", gap: "6px 12px", fontSize: 13 },
  link        : { color: "#38bdf8" },
  error       : { color: "#f87171", fontSize: 13 },
  table       : { width: "100%", borderCollapse: "collapse", fontSize: 13 },
};
