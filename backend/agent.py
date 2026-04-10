"""
NexaVault – AI Trading Agent
==============================
Decides whether to BUY, SELL, or HOLD based on price data.

Architecture
------------
Two interchangeable strategy layers are provided:

  1. RuleBasedStrategy  – deterministic threshold logic (production default)
  2. MLStrategy         – plug-in hook for FinRL / any sklearn-compatible model

Select via environment variable:   AGENT_STRATEGY=rule|ml
When AGENT_STRATEGY=ml, the agent tries to load the model at MODEL_PATH;
falls back to rule-based if the model file is absent.

All strategies must implement:
    def decide(self, price_data: dict, state: dict) -> AgentDecision
"""

import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Protocol, List

logger = logging.getLogger("nexavault.agent")


# ─────────────────────────────────────────────
# Types
# ─────────────────────────────────────────────

class Action(str, Enum):
    BUY  = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass
class AgentDecision:
    """Structured result returned by every strategy."""
    action        : Action
    confidence    : float          # 0.0 – 1.0
    reason        : str
    price_usd     : float
    price_contract: int
    metadata      : dict = field(default_factory=dict)


# ─────────────────────────────────────────────
# Strategy protocol (interface)
# ─────────────────────────────────────────────

class TradingStrategy(Protocol):
    def decide(self, price_data: dict, state: dict) -> AgentDecision:
        ...


# ─────────────────────────────────────────────
# 1. Rule-Based Strategy
# ─────────────────────────────────────────────

class RuleBasedStrategy:
    """
    Simple threshold strategy with momentum guard.

    Rules
    -----
    BUY  : current price ≤ buy_threshold  AND momentum is not strongly negative
    SELL : current price ≥ sell_threshold AND momentum is not strongly positive
    HOLD : everything else

    Thresholds can be overridden via environment variables (in USD):
        BUY_THRESHOLD_USD  (default: 0.15)
        SELL_THRESHOLD_USD (default: 0.22)
    """

    def __init__(self):
        self.buy_threshold  = float(os.getenv("BUY_THRESHOLD_USD",  "0.15"))
        self.sell_threshold = float(os.getenv("SELL_THRESHOLD_USD", "0.22"))
        self._price_history : List[float] = []   # rolling window for momentum
        self._window_size   = 5

    # ── Private helpers ──────────────────────────────────────────────────

    def _update_history(self, price: float) -> None:
        self._price_history.append(price)
        if len(self._price_history) > self._window_size:
            self._price_history.pop(0)

    def _momentum(self) -> float:
        """Return average price change over window. Positive = rising market."""
        if len(self._price_history) < 2:
            return 0.0
        deltas = [
            self._price_history[i] - self._price_history[i - 1]
            for i in range(1, len(self._price_history))
        ]
        return sum(deltas) / len(deltas)

    # ── Public interface ─────────────────────────────────────────────────

    def decide(self, price_data: dict, state: dict) -> AgentDecision:
        """
        Evaluate price data and return a trading decision.

        Args:
            price_data: Output of price_feed.get_algo_price()
            state     : Optional extra context (e.g. vault balance, last action)

        Returns:
            AgentDecision
        """
        price   = price_data["price_usd"]
        p_int   = price_data["price_contract"]

        self._update_history(price)
        mom = self._momentum()

        logger.debug(
            "RuleAgent: price=$%.6f buy_threshold=$%.4f sell_threshold=$%.4f momentum=%.8f",
            price, self.buy_threshold, self.sell_threshold, mom,
        )

        # ── Decision logic ───────────────────────────────────────────────
        if price <= self.buy_threshold:
            # Don't buy into a strongly falling market (momentum guard)
            if mom < -0.005:
                return AgentDecision(
                    action=Action.HOLD,
                    confidence=0.55,
                    reason=(
                        f"Price ${price:.4f} ≤ buy threshold ${self.buy_threshold}, "
                        f"but momentum {mom:.6f} is too negative – waiting."
                    ),
                    price_usd=price,
                    price_contract=p_int,
                    metadata={"momentum": mom},
                )
            return AgentDecision(
                action=Action.BUY,
                confidence=min(0.95, 0.70 + abs(mom) * 10),
                reason=(
                    f"Price ${price:.4f} ≤ buy threshold ${self.buy_threshold}. "
                    f"Momentum: {mom:.6f}. Triggering BUY."
                ),
                price_usd=price,
                price_contract=p_int,
                metadata={"momentum": mom},
            )

        if price >= self.sell_threshold:
            # Don't sell into a strongly rising market
            if mom > 0.005:
                return AgentDecision(
                    action=Action.HOLD,
                    confidence=0.55,
                    reason=(
                        f"Price ${price:.4f} ≥ sell threshold ${self.sell_threshold}, "
                        f"but momentum {mom:.6f} is positive – holding."
                    ),
                    price_usd=price,
                    price_contract=p_int,
                    metadata={"momentum": mom},
                )
            return AgentDecision(
                action=Action.SELL,
                confidence=min(0.95, 0.70 + abs(mom) * 10),
                reason=(
                    f"Price ${price:.4f} ≥ sell threshold ${self.sell_threshold}. "
                    f"Momentum: {mom:.6f}. Triggering SELL."
                ),
                price_usd=price,
                price_contract=p_int,
                metadata={"momentum": mom},
            )

        return AgentDecision(
            action=Action.HOLD,
            confidence=0.80,
            reason=(
                f"Price ${price:.4f} is between thresholds "
                f"[${self.buy_threshold} – ${self.sell_threshold}]. HOLD."
            ),
            price_usd=price,
            price_contract=p_int,
            metadata={"momentum": mom},
        )


# ─────────────────────────────────────────────
# 2. ML Strategy (FinRL / sklearn plug-in hook)
# ─────────────────────────────────────────────

class MLStrategy:
    """
    ML-powered strategy. Loads a pre-trained model and uses it for inference.

    Training integration
    --------------------
    To plug in a FinRL model:
      1. Train your model externally and pickle/save it.
      2. Set MODEL_PATH env var to the saved file.
      3. Override _build_features() to match your training features.
      4. Override _map_output() to map model output → Action.

    Falls back to RuleBasedStrategy if no model is found.
    """

    MODEL_PATH = os.getenv("MODEL_PATH", "models/nexavault_agent.pkl")

    def __init__(self):
        self._model    = self._load_model()
        self._fallback = RuleBasedStrategy()

    def _load_model(self):
        """Attempt to load the pickled model. Return None if unavailable."""
        import pickle
        if not os.path.isfile(self.MODEL_PATH):
            logger.warning(
                "MLStrategy: model not found at %s – will use rule-based fallback",
                self.MODEL_PATH,
            )
            return None
        try:
            with open(self.MODEL_PATH, "rb") as fh:
                model = pickle.load(fh)
            logger.info("MLStrategy: model loaded from %s", self.MODEL_PATH)
            return model
        except Exception as exc:
            logger.error("MLStrategy: failed to load model – %s", exc)
            return None

    def _build_features(self, price_data: dict, state: dict) -> list:
        """
        Convert raw price + state into the feature vector expected by the model.
        Override this method when swapping in a different model architecture.
        """
        return [
            price_data.get("price_usd", 0.0),
            price_data.get("price_contract", 0),
            state.get("vault_balance", 0),
            state.get("trade_count", 0),
        ]

    def _map_output(self, model_output) -> Action:
        """Map numeric model output to Action enum.  Adjust per model convention."""
        mapping = {0: Action.HOLD, 1: Action.BUY, 2: Action.SELL}
        return mapping.get(int(model_output), Action.HOLD)

    def decide(self, price_data: dict, state: dict) -> AgentDecision:
        if self._model is None:
            logger.debug("MLStrategy: delegating to rule-based fallback")
            return self._fallback.decide(price_data, state)

        try:
            features = self._build_features(price_data, state)
            raw      = self._model.predict([features])[0]
            action   = self._map_output(raw)
            logger.info("MLStrategy: model predicted action=%s", action)
            return AgentDecision(
                action=action,
                confidence=0.75,   # placeholder – use predict_proba if available
                reason=f"ML model decision: {action.value}",
                price_usd=price_data["price_usd"],
                price_contract=price_data["price_contract"],
                metadata={"raw_output": raw},
            )
        except Exception as exc:
            logger.error("MLStrategy inference error: %s – falling back", exc)
            return self._fallback.decide(price_data, state)


# ─────────────────────────────────────────────
# Factory
# ─────────────────────────────────────────────

def build_agent() -> TradingStrategy:
    """Instantiate the correct strategy based on AGENT_STRATEGY env var."""
    strategy = os.getenv("AGENT_STRATEGY", "rule").lower()
    if strategy == "ml":
        logger.info("Agent: using MLStrategy")
        return MLStrategy()
    logger.info("Agent: using RuleBasedStrategy")
    return RuleBasedStrategy()


# Singleton used by the FastAPI app
_agent: Optional[TradingStrategy] = None


def get_agent() -> TradingStrategy:
    """Return (or create) the global agent singleton."""
    global _agent
    if _agent is None:
        _agent = build_agent()
    return _agent
