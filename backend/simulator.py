"""
NexaVault – Trading Simulator
==============================
Simulates trades without executing on-chain transactions.
Useful for backtesting and demo purposes.
"""

import logging
import random
import time
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum
import math

logger = logging.getLogger("nexavault.simulator")


class SimulationMode(str, Enum):
    HISTORIC = "historic"      # Use historical data
    RANDOM = "random"          # Random price fluctuations
    SINE = "sine"              # Sine wave price movements
    MANUAL = "manual"          # User-controlled price


@dataclass
class SimulatedTrade:
    """A simulated trade execution."""
    timestamp: float
    action: str                 # "buy" | "sell"
    amount: float              # ALGO amount
    price: float               # USD price per ALGO
    total: float               # amount * price
    slippage: float            # Actual slippage applied
    confidence: float          # AI confidence 0-1


@dataclass
class SimulatorState:
    """Current state of the simulator."""
    balance_algo: float = 10.0          # ALGO holdings
    balance_usdc: float = 100.0         # USDC holdings
    current_price: float = 0.175        # Current ALGO/USD price
    trades: List[SimulatedTrade] = field(default_factory=list)
    total_profit_loss: float = 0.0      # Unrealized P&L
    mode: SimulationMode = SimulationMode.RANDOM
    time_acceleration: float = 1.0      # 1.0 = real-time, 10.0 = 10x faster
    paused: bool = False


class TradingSimulator:
    """
    Simulates trading scenarios without executing real transactions.
    """

    def __init__(self, 
                 initial_algo: float = 10.0,
                 initial_usdc: float = 100.0,
                 initial_price: float = 0.175,
                 mode: SimulationMode = SimulationMode.RANDOM):
        self.state = SimulatorState(
            balance_algo=initial_algo,
            balance_usdc=initial_usdc,
            current_price=initial_price,
            mode=mode,
        )
        self._price_history = [initial_price]
        self._start_time = time.time()
        logger.info("Simulator initialized: ALGO=%.2f, USDC=%.2f, Price=$%.6f",
                   initial_algo, initial_usdc, initial_price)

    # ── Price Movement ────────────────────────────────────────────────────

    def update_price(self, new_price: Optional[float] = None) -> float:
        """
        Update the current price.

        Args:
            new_price: If provided, use this price. Otherwise, generate next price.

        Returns:
            New price
        """
        if new_price is not None:
            # Manual price update
            self.state.current_price = new_price
        elif self.state.mode == SimulationMode.RANDOM:
            # Random walk
            change = random.uniform(-0.002, 0.002)  # ±0.2%
            self.state.current_price = max(0.01, self.state.current_price * (1 + change))
        elif self.state.mode == SimulationMode.SINE:
            # Sine wave oscillation
            t = time.time() - self._start_time
            oscillation = 0.02 * math.sin(t / 60)  # ±2% oscillation per minute
            base = 0.175
            self.state.current_price = base + oscillation
        # HISTORIC mode would use pre-loaded historical data

        self._price_history.append(self.state.current_price)
        return self.state.current_price

    # ── Trading Simulation ────────────────────────────────────────────────

    def buy(self, amount_algo: float, target_price: Optional[float] = None,
            slippage: float = 0.01, confidence: float = 0.8) -> Optional[SimulatedTrade]:
        """
        Simulate buying ALGO.

        Args:
            amount_algo: ALGO amount to buy
            target_price: Optional target price (if None, use current)
            slippage: Expected slippage %
            confidence: AI confidence 0-1

        Returns:
            Simulated trade or None if insufficient balance
        """
        if self.state.paused:
            logger.warning("Simulator is paused")
            return None

        price = target_price or self.state.current_price
        actual_price = price * (1 + slippage)
        cost_usdc = amount_algo * actual_price

        if cost_usdc > self.state.balance_usdc:
            logger.warning("Insufficient USDC balance: need %.2f, have %.2f",
                          cost_usdc, self.state.balance_usdc)
            return None

        # Execute trade
        self.state.balance_usdc -= cost_usdc
        self.state.balance_algo += amount_algo

        trade = SimulatedTrade(
            timestamp=time.time(),
            action="buy",
            amount=amount_algo,
            price=actual_price,
            total=cost_usdc,
            slippage=slippage,
            confidence=confidence,
        )

        self.state.trades.append(trade)
        logger.info("BUY: %.2f ALGO @ $%.6f = $%.2f (slippage: %.2f%%)",
                   amount_algo, actual_price, cost_usdc, slippage * 100)

        return trade

    def sell(self, amount_algo: float, target_price: Optional[float] = None,
             slippage: float = 0.01, confidence: float = 0.8) -> Optional[SimulatedTrade]:
        """
        Simulate selling ALGO.

        Args:
            amount_algo: ALGO amount to sell
            target_price: Optional target price (if None, use current)
            slippage: Expected slippage %
            confidence: AI confidence 0-1

        Returns:
            Simulated trade or None if insufficient balance
        """
        if self.state.paused:
            logger.warning("Simulator is paused")
            return None

        price = target_price or self.state.current_price
        actual_price = price * (1 - slippage)

        if amount_algo > self.state.balance_algo:
            logger.warning("Insufficient ALGO balance: need %.2f, have %.2f",
                          amount_algo, self.state.balance_algo)
            return None

        # Execute trade
        self.state.balance_algo -= amount_algo
        proceeds_usdc = amount_algo * actual_price
        self.state.balance_usdc += proceeds_usdc

        trade = SimulatedTrade(
            timestamp=time.time(),
            action="sell",
            amount=amount_algo,
            price=actual_price,
            total=proceeds_usdc,
            slippage=slippage,
            confidence=confidence,
        )

        self.state.trades.append(trade)
        logger.info("SELL: %.2f ALGO @ $%.6f = $%.2f (slippage: %.2f%%)",
                   amount_algo, actual_price, proceeds_usdc, slippage * 100)

        return trade

    # ── Portfolio Metrics ─────────────────────────────────────────────────

    def get_total_value(self) -> float:
        """Calculate total portfolio value in USDC."""
        algo_value = self.state.balance_algo * self.state.current_price
        return self.state.balance_usdc + algo_value

    def get_portfolio_composition(self) -> dict:
        """Get portfolio breakdown."""
        total = self.get_total_value()
        usdc_pct = (self.state.balance_usdc / total * 100) if total > 0 else 0
        algo_pct = 100 - usdc_pct

        return {
            "total_value_usdc": round(total, 2),
            "balance_algo": round(self.state.balance_algo, 4),
            "balance_usdc": round(self.state.balance_usdc, 2),
            "usdc_percentage": round(usdc_pct, 1),
            "algo_percentage": round(algo_pct, 1),
            "algo_value": round(self.state.balance_algo * self.state.current_price, 2),
        }

    def get_pnl(self) -> dict:
        """Calculate profit/loss."""
        if not self.state.trades:
            return {"realized_pnl": 0, "unrealized_pnl": 0, "total_pnl": 0}

        # Calculate realized P&L from closed positions
        # (simplified: based on buy/sell pairs)
        total_cost = sum(t.total for t in self.state.trades if t.action == "buy")
        total_proceeds = sum(t.total for t in self.state.trades if t.action == "sell")
        realized_pnl = total_proceeds - total_cost

        # Unrealized P&L on current holdings
        current_algo_value = self.state.balance_algo * self.state.current_price
        unrealized_pnl = current_algo_value - (self.state.balance_algo * 0.175)  # 0.175 is entry price

        return {
            "realized_pnl": round(realized_pnl, 2),
            "unrealized_pnl": round(unrealized_pnl, 2),
            "total_pnl": round(realized_pnl + unrealized_pnl, 2),
            "num_trades": len(self.state.trades),
        }

    # ── State Management ──────────────────────────────────────────────────

    def get_state(self) -> dict:
        """Get current simulator state."""
        return {
            "price": round(self.state.current_price, 6),
            "portfolio": self.get_portfolio_composition(),
            "pnl": self.get_pnl(),
            "mode": self.state.mode.value,
            "paused": self.state.paused,
            "trades_count": len(self.state.trades),
        }

    def pause(self):
        """Pause trading."""
        self.state.paused = True
        logger.info("Simulator paused")

    def resume(self):
        """Resume trading."""
        self.state.paused = False
        logger.info("Simulator resumed")

    def reset(self, initial_algo: float = 10.0, initial_usdc: float = 100.0,
              initial_price: float = 0.175):
        """Reset simulator to initial state."""
        self.state = SimulatorState(
            balance_algo=initial_algo,
            balance_usdc=initial_usdc,
            current_price=initial_price,
            mode=self.state.mode,
        )
        self._price_history = [initial_price]
        self._start_time = time.time()
        logger.info("Simulator reset")

    def get_trade_history(self, limit: int = 50) -> List[dict]:
        """Get recent trade history."""
        trades = self.state.trades[-limit:]
        return [
            {
                "timestamp": t.timestamp,
                "action": t.action,
                "amount": t.amount,
                "price": t.price,
                "total": t.total,
                "slippage": t.slippage,
                "confidence": t.confidence,
            }
            for t in trades
        ]


# Singleton instance
_simulator: Optional[TradingSimulator] = None


def get_simulator(mode: SimulationMode = SimulationMode.RANDOM) -> TradingSimulator:
    """Get or create the global simulator."""
    global _simulator
    if _simulator is None:
        _simulator = TradingSimulator(mode=mode)
    return _simulator


def reset_simulator(mode: SimulationMode = SimulationMode.RANDOM):
    """Reset the global simulator."""
    global _simulator
    _simulator = TradingSimulator(mode=mode)
