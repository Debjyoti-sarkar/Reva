/**
 * NexaVault – Voice Command Panel
 * ================================
 * Voice input interface for trading commands.
 * Uses Web Speech API for speech recognition.
 */

import React, { useState, useRef, useEffect } from "react";

const API_BASE = process.env.REACT_APP_API_URL ?? "http://localhost:8000";

export default function VoicePanel() {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [lastCommand, setLastCommand] = useState(null);
  const [error, setError] = useState(null);
  const [results, setResults] = useState([]);
  const recognitionRef = useRef(null);
  const [isBrowserSupported, setIsBrowserSupported] = useState(true);

  // Initialize Web Speech API
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setIsBrowserSupported(false);
      setError("Speech Recognition not supported in this browser");
      return;
    }

    recognitionRef.current = new SpeechRecognition();
    const recognition = recognitionRef.current;

    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.language = "en-US";

    recognition.onstart = () => {
      setIsListening(true);
      setTranscript("");
      setError(null);
    };

    recognition.onresult = (event) => {
      let interim = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const text = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          // Send final transcript to backend
          sendVoiceCommand(text);
        } else {
          interim += text + " ";
        }
      }
      setTranscript(interim || transcript);
    };

    recognition.onerror = (event) => {
      setError(`Speech error: ${event.error}`);
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    return () => {
      recognition.stop();
    };
  }, []);

  // Send voice command to backend
  const sendVoiceCommand = async (voiceText) => {
    if (!voiceText.trim()) return;

    setTranscript(voiceText);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/voice/parse`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ voice_text: voiceText }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      setLastCommand(data);

      // Add to results history
      setResults((prev) => [{ text: voiceText, result: data, time: new Date() }, ...prev].slice(0, 10));

      // Provide audio feedback
      speakFeedback(data);
    } catch (err) {
      setError(`Failed to process voice command: ${err.message}`);
    }
  };

  // Text-to-speech feedback
  const speakFeedback = (commandData) => {
    const synth = window.speechSynthesis;
    if (!synth) return;

    let message = "";
    if (commandData.error_message) {
      message = `Error: ${commandData.error_message}`;
    } else {
      switch (commandData.command_type) {
        case "buy":
          message = `Buying ${commandData.amount} ALGO at ${commandData.target_price}`;
          break;
        case "sell":
          message = `Selling ${commandData.amount} ALGO at ${commandData.target_price}`;
          break;
        case "balance":
          message = "Fetching wallet balance";
          break;
        case "price":
          message = "Getting current price";
          break;
        case "status":
          message = "Checking trading status";
          break;
        case "simulate":
          message = `Starting simulation with ${commandData.amount} trades`;
          break;
        default:
          message = "Command received";
      }
    }

    const utterance = new SpeechSynthesisUtterance(message);
    utterance.rate = 1.0;
    synth.speak(utterance);
  };

  const startListening = () => {
    if (recognitionRef.current) {
      recognitionRef.current.start();
    }
  };

  const stopListening = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
  };

  const handleManualCommand = (e) => {
    if (e.key === "Enter") {
      sendVoiceCommand(transcript);
    }
  };

  if (!isBrowserSupported) {
    return (
      <div style={styles.panel}>
        <h3 style={styles.title}>🎤 Voice Commands - Not Supported</h3>
        <p style={styles.error}>Your browser doesn't support Speech Recognition.</p>
        <p style={styles.sub}>Try Chrome, Edge, or Safari.</p>
      </div>
    );
  }

  return (
    <div style={styles.panel}>
      {/* Header */}
      <div style={styles.header}>
        <h3 style={styles.title}>🎤 Voice Commands</h3>
        <p style={styles.sub}>Say: "buy 1 ALGO at 0.15" or "sell 2 ALGO at 0.22"</p>
      </div>

      {/* Transcript Display */}
      <div style={styles.transcriptBox}>
        <div style={styles.transcriptLabel}>
          {isListening ? "🔴 Listening..." : "Transcript"}
        </div>
        <input
          type="text"
          value={transcript}
          onChange={(e) => setTranscript(e.target.value)}
          onKeyPress={handleManualCommand}
          placeholder="Say something or type here..."
          style={styles.transcriptInput}
        />
      </div>

      {/* Controls */}
      <div style={styles.controls}>
        <button
          onClick={startListening}
          disabled={isListening}
          style={{
            ...styles.button,
            ...(isListening && styles.buttonDisabled),
            background: isListening ? "#94a3b8" : "#22c55e",
          }}
        >
          {isListening ? "🎙️ Recording..." : "🎤 Start Listening"}
        </button>
        <button
          onClick={stopListening}
          disabled={!isListening}
          style={{
            ...styles.button,
            ...(isListening ? {} : styles.buttonDisabled),
            background: isListening ? "#ef4444" : "#94a3b8",
          }}
        >
          ⏹️ Stop
        </button>
        <button
          onClick={() => sendVoiceCommand(transcript)}
          disabled={!transcript.trim()}
          style={styles.button}
        >
          ✨ Parse Command
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div style={styles.errorBox}>
          <strong>❌ Error:</strong> {error}
        </div>
      )}

      {/* Last Command Result */}
      {lastCommand && (
        <div
          style={{
            ...styles.resultBox,
            borderLeft: lastCommand.error_message ? "4px solid #f87171" : "4px solid #22c55e",
          }}
        >
          <div style={styles.resultTitle}>
            📝 Parsed Command ({Math.round(lastCommand.confidence * 100)}% confidence)
          </div>
          <div style={styles.resultContent}>
            <div>
              <strong>Type:</strong> <code>{lastCommand.command_type}</code>
            </div>
            {lastCommand.amount && <div><strong>Amount:</strong> {lastCommand.amount}</div>}
            {lastCommand.target_price && (
              <div><strong>Target Price:</strong> ${lastCommand.target_price}</div>
            )}
            {lastCommand.error_message && (
              <div style={{ color: "#f87171" }}>
                <strong>Error:</strong> {lastCommand.error_message}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Results History */}
      {results.length > 0 && (
        <div style={styles.historyBox}>
          <div style={styles.historyTitle}>📋 Command History</div>
          <div style={styles.historyList}>
            {results.map((item, idx) => (
              <div key={idx} style={styles.historyItem}>
                <div style={styles.historyTime}>
                  {item.time.toLocaleTimeString()}
                </div>
                <div style={styles.historyText}>{item.text}</div>
                <div style={styles.historyType}>
                  {item.result.command_type} {item.result.error_message ? "❌" : "✅"}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Examples */}
      <div style={styles.examplesBox}>
        <div style={styles.examplesTitle}>💡 Command Examples:</div>
        <ul style={styles.examplesList}>
          <li>"Buy 1 ALGO at 0.15"</li>
          <li>"Sell 2 ALGO at 0.22"</li>
          <li>"What's my balance"</li>
          <li>"What's the current price"</li>
          <li>"Show trading status"</li>
          <li>"Simulate 5 trades"</li>
        </ul>
      </div>
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
  title: {
    margin: 0,
    fontSize: 16,
    fontWeight: 700,
    marginBottom: 4,
  },
  sub: { margin: 0, fontSize: 12, color: "#94a3b8" },

  transcriptBox: { marginBottom: 14 },
  transcriptLabel: { fontSize: 12, color: "#94a3b8", marginBottom: 6, fontWeight: 600 },
  transcriptInput: {
    width: "100%",
    padding: "10px 12px",
    background: "#0f172a",
    border: "1px solid #334155",
    borderRadius: 8,
    color: "#e2e8f0",
    fontSize: 14,
    boxSizing: "border-box",
  },

  controls: {
    display: "flex",
    gap: 8,
    marginBottom: 16,
    flexWrap: "wrap",
  },
  button: {
    background: "#0ea5e9",
    color: "#fff",
    border: "none",
    borderRadius: 8,
    padding: "10px 16px",
    fontWeight: 600,
    cursor: "pointer",
    fontSize: 12,
  },
  buttonDisabled: { opacity: 0.5, cursor: "not-allowed" },

  errorBox: {
    background: "#7f1d1d",
    borderLeft: "4px solid #dc2626",
    padding: 12,
    borderRadius: 6,
    marginBottom: 12,
    fontSize: 12,
  },

  resultBox: {
    background: "#0f172a",
    padding: 12,
    borderRadius: 8,
    marginBottom: 12,
    fontSize: 12,
  },
  resultTitle: { fontWeight: 700, marginBottom: 8, color: "#38bdf8" },
  resultContent: { display: "flex", flexDirection: "column", gap: 4 },

  historyBox: {
    background: "#0f172a",
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
    fontSize: 11,
  },
  historyTitle: { fontWeight: 700, marginBottom: 8, color: "#38bdf8" },
  historyList: { display: "flex", flexDirection: "column", gap: 6, maxHeight: 200, overflowY: "auto" },
  historyItem: {
    background: "#1e293b",
    padding: 8,
    borderRadius: 4,
    display: "grid",
    gridTemplateColumns: "60px 1fr 80px",
    gap: 8,
    alignItems: "center",
  },
  historyTime: { color: "#64748b", fontSize: 10 },
  historyText: { color: "#cbd5e1", overflowX: "auto", whiteSpace: "nowrap" },
  historyType: { color: "#94a3b8", textAlign: "right" },

  examplesBox: {
    background: "#1e293b",
    borderRadius: 8,
    padding: 12,
    fontSize: 12,
  },
  examplesTitle: { fontWeight: 700, marginBottom: 8, color: "#38bdf8" },
  examplesList: { margin: 0, paddingLeft: 20, color: "#cbd5e1" },
};
