import React, { useState } from "react";
import { PeraWalletConnect } from "@perawallet/connect";

const peraWallet = new PeraWalletConnect();

function App() {
  const [account, setAccount] = useState(null);

  const connectWallet = async () => {
    try {
      const accounts = await peraWallet.connect();
      setAccount(accounts[0]);
      console.log("Connected:", accounts[0]);
    } catch (err) {
      console.error(err);
    }
  };

  const startTrading = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/trade", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          action: "buy",
          amount_microalgo: 1000000,
          user_address: account,
        }),
      });

      const data = await res.json();
      console.log("Backend:", data);

      if (data.transactions) {
        const txns = data.transactions.map((txn) => ({
          txn: txn,
          signers: [account],
        }));

        const signedTxns = await peraWallet.signTransaction([txns]);

        console.log("Signed:", signedTxns);
        alert("Transaction signed! 🚀");
      }
    } catch (err) {
      console.error(err);
      alert("Error ❌");
    }
  };

  return (
    <div style={{ padding: 20 }}>
      <h1>🚀 NexaVault</h1>

      <button onClick={connectWallet}>
        {account ? "Connected ✅" : "Connect Pera Wallet"}
      </button>

      <br /><br />

      <button onClick={startTrading} disabled={!account}>
        Start Auto Trading
      </button>
    </div>
  );
}

export default App;