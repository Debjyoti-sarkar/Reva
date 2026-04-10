/**
 * NexaVault – Pera Wallet Connector
 * ===================================
 * Wraps @perawallet/connect to provide a clean React hook + context
 * for connecting to Pera Wallet on Algorand Testnet.
 *
 * Usage:
 *   import { usePeraWallet } from './peraConnect';
 *   const { connect, disconnect, accounts, isConnected } = usePeraWallet();
 *
 * @see https://github.com/perawallet/connect
 */

import { useState, useCallback, useEffect, createContext, useContext } from "react";
import { PeraWalletConnect } from "@perawallet/connect";

// ── Pera Wallet instance (singleton) ────────────────────────────────────────
const peraWallet = new PeraWalletConnect({
  shouldShowSignTxnToast: true,     // show native "Sign transaction" toast
  chainId: 416002,                  // 416001 = mainnet | 416002 = testnet
});

// ── Context ──────────────────────────────────────────────────────────────────
const PeraWalletContext = createContext(null);

/**
 * Provider – wrap your app in this to give all children access to the wallet.
 *
 * <PeraWalletProvider>
 *   <App />
 * </PeraWalletProvider>
 */
export function PeraWalletProvider({ children }) {
  const wallet = usePeraWalletInternal();
  return (
    <PeraWalletContext.Provider value={wallet}>
      {children}
    </PeraWalletContext.Provider>
  );
}

/**
 * Hook – consume the wallet context from any child component.
 */
export function usePeraWallet() {
  const ctx = useContext(PeraWalletContext);
  if (!ctx) {
    throw new Error("usePeraWallet must be used inside <PeraWalletProvider>");
  }
  return ctx;
}


// ── Internal hook (used by the provider) ────────────────────────────────────

function usePeraWalletInternal() {
  const [accounts, setAccounts]       = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setConnecting] = useState(false);
  const [error, setError]             = useState(null);

  // ── Reconnect on mount (if user was already connected) ─────────────────
  useEffect(() => {
    peraWallet
      .reconnectSession()
      .then((addrs) => {
        if (addrs && addrs.length > 0) {
          setAccounts(addrs);
          setIsConnected(true);
        }
      })
      .catch(() => {
        // No previous session – normal
      });

    // ── Listen for disconnect events ──────────────────────────────────────
    peraWallet.connector?.on("disconnect", handleDisconnect);

    return () => {
      peraWallet.connector?.off("disconnect", handleDisconnect);
    };
  }, []);

  // ── Handlers ──────────────────────────────────────────────────────────────

  const handleDisconnect = useCallback(() => {
    setAccounts([]);
    setIsConnected(false);
    setError(null);
  }, []);

  /**
   * Initiate a new Pera Wallet connection.
   * Opens the QR modal or deep-links to the Pera app.
   */
  const connect = useCallback(async () => {
    setConnecting(true);
    setError(null);
    try {
      const newAccounts = await peraWallet.connect();
      setAccounts(newAccounts);
      setIsConnected(true);

      // Re-register disconnect listener after new connection
      peraWallet.connector?.on("disconnect", handleDisconnect);
    } catch (err) {
      if (err?.data?.type !== "CONNECT_MODAL_CLOSED") {
        // Only surface real errors, not user-initiated modal closes
        console.error("Pera Wallet connect error:", err);
        setError(err?.message ?? "Failed to connect wallet");
      }
    } finally {
      setConnecting(false);
    }
  }, [handleDisconnect]);

  /**
   * Disconnect the current Pera Wallet session.
   */
  const disconnect = useCallback(async () => {
    try {
      await peraWallet.disconnect();
    } catch (err) {
      console.warn("Disconnect error (non-fatal):", err);
    } finally {
      handleDisconnect();
    }
  }, [handleDisconnect]);

  /**
   * Sign a group of transactions using Pera Wallet.
   *
   * @param {Array<{txn: algosdk.Transaction, signers: string[]}>} txnGroup
   * @returns {Promise<Uint8Array[]>} signed transaction bytes
   */
  const signTransactions = useCallback(async (txnGroup) => {
    if (!isConnected) throw new Error("Wallet not connected");
    try {
      const signed = await peraWallet.signTransaction([txnGroup]);
      return signed;
    } catch (err) {
      console.error("Pera Wallet sign error:", err);
      throw err;
    }
  }, [isConnected]);

  return {
    /** Array of connected Algorand addresses */
    accounts,
    /** Primary (first) connected address */
    address: accounts[0] ?? null,
    /** True when at least one account is connected */
    isConnected,
    /** True during the connect() async operation */
    isConnecting,
    /** Last connection error (string or null) */
    error,
    /** Connect to Pera Wallet */
    connect,
    /** Disconnect from Pera Wallet */
    disconnect,
    /** Sign transaction group */
    signTransactions,
    /** Raw Pera SDK instance (for advanced use) */
    peraWallet,
  };
}
