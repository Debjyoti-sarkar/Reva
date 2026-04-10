/**
 * NexaVault – React App Root
 * ============================
 * Wraps the app in the PeraWalletProvider and renders the Dashboard.
 *
 * To start the frontend:
 *   cd frontend && npm install && npm start
 *
 * Environment variables (create frontend/.env):
 *   REACT_APP_API_URL=http://localhost:8000
 *   REACT_APP_AUTO_TRADE_INTERVAL=60000
 */

import React from "react";
import ReactDOM from "react-dom/client";
import { PeraWalletProvider } from "./peraConnect";
import Dashboard from "./Dashboard";

// ── Global reset + dark background ──────────────────────────────────────────
const globalStyles = `
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: #0f172a;
    color: #e2e8f0;
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
    -webkit-font-smoothing: antialiased;
  }
  a { color: #38bdf8; }
  button:disabled { opacity: 0.5; cursor: not-allowed !important; }
`;

const styleEl = document.createElement("style");
styleEl.textContent = globalStyles;
document.head.appendChild(styleEl);

// ── Mount ─────────────────────────────────────────────────────────────────────
const root = ReactDOM.createRoot(document.getElementById("root"));

root.render(
  <React.StrictMode>
    <PeraWalletProvider>
      <Dashboard />
    </PeraWalletProvider>
  </React.StrictMode>
);
