/**
 * NexaVault – Trading Simulator
 * =============================
 * Web-based simulator for backtesting and demo trading without real funds.
 */

import React, { useState, useEffect, useCallback } from "react";

const API_BASE = process.env.REACT_APP_API_URL ?? "http://localhost:8000";

export default function SimulatorPanel() {
  const [simulatorMode, setSimulatorMode] = useState("random");
  const [isRunning, setIsRunning] = useState(false);
  const [price, setPrice] = useState(0.175);
  const [portfolio, setPortfolio] = useState(null);
  const [pnl, setPnl] = useState(null);
  const [trades, setTrades] = useState([]);
  const [error, setError] = useState(null);
  const [lastAction, setLastAction] = useState(null);

  // ── Fetch Simulator State ─────────────────────────────────────────────
  const fetchState = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/simulator/state`);
      if (!res.ok) throw new Error("Failed to fetch simulator state");
      const data = await res.json();
      setPrice(data.price);
      setPortfolio(data.portfolio);
      setPnl(data.pnl);
    } catch (err) {
      setError(err.message);
    }
  }, []);

  // ── Fetch Trade History ───────────────────────────────────────────────
  const fetchTrades = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/simulator/trades`);
      if (!res.ok) throw new Error("Failed to fetch trades");
      const data = await res.json();
      setTrades(data.trades || []);
    } catch (err) {
      setError(err.message);
    }
  }, []);

  // ── Initialize Simulator ──────────────────────────────────────────────
  useEffect(() => {
    fetchState();
    fetchTrades();
  }, [fetchState, fetchTrades]);

  // ── Update Price (Manual or Auto) ─────────────────────────────────────
  const updatePrice = async (newPrice) => {
    try {
      const res = await fetch(`${API_BASE}/simulator/price`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ price: newPrice, mode: simulatorMode }),
      });
      if (res.ok) {
        const data = await res.json();
        setPrice(data.new_price);
      }
    } catch (err) {
      setError(err.message);
    }
  };

  // ── Execute Buy ───────────────────────────────────────────────────────
  const executeBuy = async (amount) => {
    try {
      const res = await fetch(`${API_BASE}/simulator/buy`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ amount_algo: amount, confidence: 0.9 }),
      });
      if (!res.ok) throw new Error("Buy failed");
      const data = await res.json();
      setLastAction({ type: "buy", amount, price: data.price, success: true });
      fetchState();
      fetchTrades();
    } catch (err) {
      setLastAction({ type: "buy", amount, error: err.message, success: false });
      setError(err.message);
    }
  };

  // ── Execute Sell ──────────────────────────────────────────────────────
  const executeSell = async (amount) => {
    try {
      const res = await fetch(`${API_BASE}/simulator/sell`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ amount_algo: amount, confidence: 0.9 }),
      });
      if (!res.ok) throw new Error("Sell failed");
      const data = await res.json();
      setLastAction({ type: "sell", amount, price: data.price, success: true });
      fetchState();
      fetchTrades();
    } catch (err) {
      setLastAction({ type: "sell", amount, error: err.message, success: false });
      setError(err.message);
    }
  };

  // ── Toggle Auto-Simulation ────────────────────────────────────────────
  const toggleAutoSimulation = async () => {
    try {
      const res = await fetch(`${API_BASE}/simulator/auto`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enabled: !isRunning }),
      });
      if (res.ok) {
        setIsRunning(!isRunning);
      }
    } catch (err) {
      setError(err.message);
    }
  };

  // ── Reset Simulator ───────────────────────────────────────────────────
  const resetSimulator = async () => {
    try {
      const res = await fetch(`${API_BASE}/simulator/reset`, { method: "POST" });
      if (res.ok) {
        setTrades([]);
        setPnl(null);
        setLastAction(null);
        fetchState();
      }
    } catch (err) {
      setError(err.message);
    }
  };

  if (!portfolio) {
    return <div style={styles.panel}>Loading simulator...</div>;
  }

  return (
    <div style={styles.panel}>
      {/* Header */}
      <div style={styles.header}>
        <h3 style={styles.title}>🎮 Trading Simulator</h3>
        <p style={styles.sub}>Test trading strategies without real funds</p>
      </div>

      {/* Price Display */}
      <div style={styles.priceCard}>
        <div style={styles.priceLabel}>ALGO / USD</div>
        <div style={styles.priceValue}>${price.toFixed(6)}</div>
        <div style={styles.priceControls}>
          <input
            type="range"
            min="0.05"
            max="0.5"
            step="0.001"
            value={price}
            onChange={(e) => updatePrice(parseFloat(e.target.value))}
            style={styles.priceSlider}
          />
          <div style={styles.priceRange}>
            <span>$0.05</span>
            <span>$0.5</span>
          </div>
        </div>
      </div>

      {/* Portfolio */}
      <div style={styles.portfolioCard}>
        <div style={styles.cardTitle}>💼 Portfolio</div>
        <div style={styles.portfolioGrid}>
          <div style={styles.portfolioItem}>
            <div style={styles.itemLabel}>Total Value</div>
            <div style={styles.itemValue}>${portfolio.total_value_usdc.toFixed(2)}</div>
          </div>
          <div style={styles.portfolioItem}>
            <div style={styles.itemLabel}>ALGO</div>
            <div style={styles.itemValue}>{portfolio.balance_algo.toFixed(4)}</div>
            <div style={styles.itemSub}>{portfolio.algo_percentage.toFixed(1)}%</div>
          </div>
          <div style={styles.portfolioItem}>
            <div style={styles.itemLabel}>USDC</div>
            <div style={styles.itemValue}>${portfolio.balance_usdc.toFixed(2)}</div>
            <div style={styles.itemSub}>{portfolio.usdc_percentage.toFixed(1)}%</div>
          </div>
        </div>
      </div>

      {/* P&L */}
      {pnl && (
        <div
          style={{
            ...styles.pnlCard,
            background: pnl.total_pnl >= 0 ? "#0f172a" : "#1e293b",
            borderLeft: `4px solid ${pnl.total_pnl >= 0 ? "#22c55e" : "#ef4444"}`,
          }}
        >
          <div style={styles.cardTitle}>📊 Profit & Loss</div>
          <div style={styles.pnlGrid}>
            <div>
              <div style={styles.itemLabel}>Realized P&L</div>
              <div style={{ color: pnl.realized_pnl >= 0 ? "#22c55e" : "#ef4444", fontWeight: 700 }}>
                ${pnl.realized_pnl.toFixed(2)}
              </div>
            </div>
            <div>
              <div style={styles.itemLabel}>Unrealized P&L</div>
              <div style={{ color: pnl.unrealized_pnl >= 0 ? "#22c55e" : "#ef4444", fontWeight: 700 }}>
                ${pnl.unrealized_pnl.toFixed(2)}
              </div>
            </div>
            <div>
              <div style={styles.itemLabel}>Total P&L</div>
              <div
                style={{
                  color: pnl.total_pnl >= 0 ? "#22c55e" : "#ef4444",
                  fontWeight: 800,
                  fontSize: 16,
                }}
              >
                ${pnl.total_pnl.toFixed(2)}
              </div>
            </div>
          </div>
          <div style={styles.tradesCount}>Trades: {pnl.num_trades}</div>
        </div>
      )}

      {/* Trading Controls */}
      <div style={styles.controlsCard}>
        <div style={styles.cardTitle}>🎮 Controls</div>

        {/* Quick Trade Buttons */}
        <div style={styles.quickTrade}>
          <div style={styles.quickLabel}>Quick Trade (1 ALGO):</div>
          <div style={styles.quickButtons}>
            <button
              onClick={() => executeBuy(1)}
              style={{ ...styles.button, background: "#22c55e" }}
            >
              🟢 Buy 1 ALGO
            </button>
            <button
              onClick={() => executeSell(1)}
              style={{ ...styles.button, background: "#ef4444" }}
            >
              🔴 Sell 1 ALGO
            </button>
          </div>
        </div>

        {/* Custom Amount */}
        <div style={styles.customTrade}>
          <input
            type="number"
            placeholder="Amount (ALGO)"
            min="0.1"
            max="10"
            step="0.1"
            id="customAmount"
            style={styles.customInput}
          />
          <button
            onClick={() => {
              const amount = parseFloat(document.getElementById("customAmount").value);
              if (amount > 0) executeBuy(amount);
            }}
            style={{ ...styles.button, background: "#22c55e" }}
          >
            💰 Buy
          </button>
          <button
            onClick={() => {
              const amount = parseFloat(document.getElementById("customAmount").value);
              if (amount > 0) executeSell(amount);
            }}
            style={{ ...styles.button, background: "#ef4444" }}
          >
            💸 Sell
          </button>
        </div>

        {/* Mode & Auto */}
        <div style={styles.modeControl}>
          <select
            value={simulatorMode}
            onChange={(e) => setSimulatorMode(e.target.value)}
            style={styles.modeSelect}
          >
            <option value="random">Random Walk</option>
            <option value="sine">Sine Wave</option>
            <option value="manual">Manual</option>
          </select>

          <button
            onClick={toggleAutoSimulation}
            style={{
              ...styles.button,
              background: isRunning ? "#ef4444" : "#22c55e",
            }}
          >
            {isRunning ? "⏹️ Stop Auto" : "▶️ Auto Trade"}
          </button>

          <button onClick={resetSimulator} style={{ ...styles.button, background: "#94a3b8" }}>
            🔄 Reset
          </button>
        </div>
      </div>

      {/* Last Action */}
      {lastAction && (
        <div
          style={{
            ...styles.actionCard,
            borderLeft: `4px solid ${lastAction.success ? "#22c55e" : "#ef4444"}`,
          }}
        >
          <div style={styles.actionLabel}>
            {lastAction.success ? "✅" : "❌"} {lastAction.type.toUpperCase()}
          </div>
          <div style={styles.actionContent}>
            {lastAction.amount && <div>Amount: {lastAction.amount} ALGO</div>}
            {lastAction.price && <div>Price: ${lastAction.price.toFixed(6)}</div>}
            {lastAction.error && <div style={{ color: "#f87171" }}>{lastAction.error}</div>}
          </div>
        </div>
      )}

      {/* Trade History */}
      {trades.length > 0 && (
        <div style={styles.historyCard}>
          <div style={styles.cardTitle}>📋 Trade History</div>
          <div style={styles.historyTable}>
            <div style={styles.historyHeader}>
              <div>Action</div>
              <div>Amount</div>
              <div>Price</div>
              <div>Total</div>
            </div>
            {trades.slice(0, 10).map((trade, idx) => (
              <div key={idx} style={styles.historyRow}>
                <div style={{ color: trade.action === "buy" ? "#22c55e" : "#ef4444" }}>
                  {trade.action === "buy" ? "🟢 BUY" : "🔴 SELL"}
                </div>
                <div>{trade.amount.toFixed(4)}</div>
                <div>${trade.price.toFixed(6)}</div>
                <div>${trade.total.toFixed(2)}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div style={styles.errorBox}>
          <strong>❌ Error:</strong> {error}
        </div>
      )}
    </div>
  );
}

const styles = {
  panel: {
    background: "#1e293b",
    borderRadius: 14,
    padding: 20,
    marginBottom: 20,
    border: "1px solid #334155",
    color: "#e2e8f0",
  },
  header: { marginBottom: 16 },
  title: { margin: 0, fontSize: 16, fontWeight: 700, marginBottom: 4 },
  sub: { margin: 0, fontSize: 12, color: "#94a3b8" },

  cardTitle: { fontSize: 12, fontWeight: 700, color: "#38bdf8", marginBottom: 10, textTransform: "uppercase" },

  priceCard: {
    background: "#0f172a",
    borderLeft: "4px solid #38bdf8",
    padding: 14,
    borderRadius: 8,
    marginBottom: 14,
  },
  priceLabel: { fontSize: 11, color: "#94a3b8", marginBottom: 4 },
  priceValue: { fontSize: 32, fontWeight: 800, color: "#38bdf8", marginBottom: 10 },
  priceControls: { display: "flex", flexDirection: "column", gap: 6 },
  priceSlider: { width: "100%", cursor: "pointer" },
  priceRange: { display: "flex", justifyContent: "space-between", fontSize: 10, color: "#64748b" },

  portfolioCard: {
    background: "#0f172a",
    borderLeft: "4px solid #22c55e",
    padding: 14,
    borderRadius: 8,
    marginBottom: 14,
  },
  pnlCard: {
    padding: 14,
    borderRadius: 8,
    marginBottom: 14,
  },
  portfolioGrid: { display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10 },
  pnlGrid: { display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10 },
  portfolioItem: { textAlign: "center" },
  itemLabel: { fontSize: 11, color: "#94a3b8", marginBottom: 4 },
  itemValue: { fontSize: 14, fontWeight: 700, color: "#e2e8f0" },
  itemSub: { fontSize: 10, color: "#64748b", marginTop: 2 },
  tradesCount: { fontSize: 11, color: "#94a3b8", marginTop: 10 },

  controlsCard: {
    background: "#0f172a",
    borderLeft: "4px solid #f59e0b",
    padding: 14,
    borderRadius: 8,
    marginBottom: 14,
  },
  quickTrade: { marginBottom: 12 },
  quickLabel: { fontSize: 11, color: "#94a3b8", marginBottom: 6 },
  quickButtons: { display: "flex", gap: 8 },
  customTrade: { display: "flex", gap: 8, marginBottom: 12 },
  customInput: {
    flex: 1,
    padding: "8px 10px",
    background: "#1e293b",
    border: "1px solid #334155",
    borderRadius: 6,
    color: "#e2e8f0",
    fontSize: 12,
  },
  modeControl: { display: "flex", gap: 8, flexWrap: "wrap" },
  modeSelect: {
    padding: "8px 10px",
    background: "#1e293b",
    border: "1px solid #334155",
    borderRadius: 6,
    color: "#e2e8f0",
    fontSize: 12,
  },
  button: {
    padding: "8px 12px",
    border: "none",
    borderRadius: 6,
    color: "#fff",
    fontWeight: 600,
    cursor: "pointer",
    fontSize: 12,
  },

  actionCard: {
    background: "#0f172a",
    padding: 12,
    borderRadius: 8,
    marginBottom: 14,
    fontSize: 12,
  },
  actionLabel: { fontWeight: 700, marginBottom: 6, color: "#38bdf8" },
  actionContent: { display: "flex", flexDirection: "column", gap: 4 },

  historyCard: {
    background: "#0f172a",
    borderLeft: "4px solid #06b6d4",
    padding: 14,
    borderRadius: 8,
  },
  historyTable: { display: "flex", flexDirection: "column", fontSize: 11 },
  historyHeader: {
    display: "grid",
    gridTemplateColumns: "repeat(4, 1fr)",
    gap: 8,
    fontWeight: 700,
    color: "#94a3b8",
    paddingBottom: 8,
    borderBottom: "1px solid #334155",
    marginBottom: 8,
  },
  historyRow: {
    display: "grid",
    gridTemplateColumns: "repeat(4, 1fr)",
    gap: 8,
    paddingBottom: 6,
    borderBottom: "1px solid #334155",
  },

  errorBox: {
    background: "#7f1d1d",
    borderLeft: "4px solid #dc2626",
    padding: 12,
    borderRadius: 6,
    fontSize: 12,
  },
};
