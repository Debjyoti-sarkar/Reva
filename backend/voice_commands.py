"""
NexaVault – Voice Command Processor
====================================
Converts voice commands into trading actions.

Examples:
  "buy 1 ALGO at 0.15"
  "sell 2 ALGO at 0.22"
  "show my balance"
  "what's the current price"
  "simulate 5 trades"
"""

import logging
import re
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any

logger = logging.getLogger("nexavault.voice_commands")


class VoiceCommandType(str, Enum):
    BUY = "buy"
    SELL = "sell"
    BALANCE = "balance"
    PRICE = "price"
    STATUS = "status"
    SIMULATE = "simulate"
    SETTINGS = "settings"
    UNKNOWN = "unknown"


@dataclass
class VoiceCommand:
    """Parsed voice command structure."""
    command_type: VoiceCommandType
    amount: Optional[float] = None          # For buy/sell
    target_price: Optional[float] = None    # For buy/sell
    action: Optional[str] = None            # Additional action
    raw_text: str = ""
    confidence: float = 0.0                 # Confidence score 0-1
    error_message: Optional[str] = None


class VoiceCommandParser:
    """
    Parses natural language voice commands into structured trading actions.
    """

    # Regex patterns for command matching
    BUY_PATTERN = r"(buy|purchase|acquire)\s+(\d+(?:\.\d+)?)\s+(algo|algos)\s+(?:at|@)?\s*(\d+(?:\.\d+)?)"
    SELL_PATTERN = r"(sell|liquidate|exit)\s+(\d+(?:\.\d+)?)\s+(algo|algos)\s+(?:at|@)?\s*(\d+(?:\.\d+)?)"
    BALANCE_PATTERN = r"(balance|account|how much|wallet|holdings?)"
    PRICE_PATTERN = r"(price|cost|rate|current|what'?s|algo price|algo rate)"
    STATUS_PATTERN = r"(status|state|summary|overview|trading status)"
    SIMULATE_PATTERN = r"(simulate|simulation|simulate trading|test|backtest|demo)\s*(\d+)?"

    def __init__(self):
        self.patterns = {
            VoiceCommandType.BUY: self.BUY_PATTERN,
            VoiceCommandType.SELL: self.SELL_PATTERN,
            VoiceCommandType.BALANCE: self.BALANCE_PATTERN,
            VoiceCommandType.PRICE: self.PRICE_PATTERN,
            VoiceCommandType.STATUS: self.STATUS_PATTERN,
            VoiceCommandType.SIMULATE: self.SIMULATE_PATTERN,
        }

    def parse(self, voice_text: str) -> VoiceCommand:
        """
        Parse voice text into a VoiceCommand object.

        Args:
            voice_text: Raw voice input string

        Returns:
            VoiceCommand with parsed data
        """
        if not voice_text or not isinstance(voice_text, str):
            return VoiceCommand(
                command_type=VoiceCommandType.UNKNOWN,
                raw_text=voice_text or "",
                error_message="Invalid input"
            )

        # Normalize input
        text = voice_text.strip().lower()
        original_text = text

        logger.info("Parsing voice command: %s", text)

        # Try matching each pattern
        for cmd_type, pattern in self.patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                logger.info("Matched command type: %s", cmd_type)
                return self._build_command(cmd_type, match, original_text)

        # No pattern matched
        return VoiceCommand(
            command_type=VoiceCommandType.UNKNOWN,
            raw_text=original_text,
            error_message=f"Unrecognized command: {original_text}",
            confidence=0.1
        )

    def _build_command(self, cmd_type: VoiceCommandType, match, raw_text: str) -> VoiceCommand:
        """Build structured command from regex match."""
        try:
            if cmd_type == VoiceCommandType.BUY:
                return VoiceCommand(
                    command_type=VoiceCommandType.BUY,
                    amount=float(match.group(2)),
                    target_price=float(match.group(4)),
                    raw_text=raw_text,
                    confidence=0.95,
                )

            elif cmd_type == VoiceCommandType.SELL:
                return VoiceCommand(
                    command_type=VoiceCommandType.SELL,
                    amount=float(match.group(2)),
                    target_price=float(match.group(4)),
                    raw_text=raw_text,
                    confidence=0.95,
                )

            elif cmd_type == VoiceCommandType.BALANCE:
                return VoiceCommand(
                    command_type=VoiceCommandType.BALANCE,
                    raw_text=raw_text,
                    confidence=0.90,
                )

            elif cmd_type == VoiceCommandType.PRICE:
                return VoiceCommand(
                    command_type=VoiceCommandType.PRICE,
                    raw_text=raw_text,
                    confidence=0.90,
                )

            elif cmd_type == VoiceCommandType.STATUS:
                return VoiceCommand(
                    command_type=VoiceCommandType.STATUS,
                    raw_text=raw_text,
                    confidence=0.90,
                )

            elif cmd_type == VoiceCommandType.SIMULATE:
                # Extract number of trades if provided
                groups = match.groups()
                num_trades = int(groups[1]) if len(groups) > 1 and groups[1] else 5
                return VoiceCommand(
                    command_type=VoiceCommandType.SIMULATE,
                    amount=float(num_trades),
                    raw_text=raw_text,
                    confidence=0.90,
                )

            else:
                return VoiceCommand(
                    command_type=VoiceCommandType.UNKNOWN,
                    raw_text=raw_text,
                    error_message=f"Unsupported command type: {cmd_type}",
                    confidence=0.5,
                )

        except (ValueError, IndexError) as e:
            logger.error("Error parsing command: %s", e)
            return VoiceCommand(
                command_type=VoiceCommandType.UNKNOWN,
                raw_text=raw_text,
                error_message=f"Parse error: {str(e)}",
                confidence=0.2,
            )

    def validate_command(self, cmd: VoiceCommand) -> tuple[bool, Optional[str]]:
        """
        Validate a parsed command.

        Returns:
            (is_valid, error_message)
        """
        if cmd.command_type == VoiceCommandType.UNKNOWN:
            return False, cmd.error_message or "Unknown command"

        if cmd.command_type in [VoiceCommandType.BUY, VoiceCommandType.SELL]:
            if cmd.amount is None or cmd.amount <= 0:
                return False, "Invalid amount"
            if cmd.target_price is None or cmd.target_price <= 0:
                return False, "Invalid target price"
            if cmd.amount > 1000:  # Sanity check
                return False, "Amount too large (max 1000 ALGO)"
            if cmd.target_price > 10:  # Sanity check
                return False, "Price seems unreasonable (max $10)"

        return True, None


# Singleton instance
_parser = VoiceCommandParser()


def parse_voice_command(voice_text: str) -> VoiceCommand:
    """Parse a voice command string."""
    return _parser.parse(voice_text)


def validate_command(cmd: VoiceCommand) -> tuple[bool, Optional[str]]:
    """Validate a voice command."""
    return _parser.validate_command(cmd)


def command_to_dict(cmd: VoiceCommand) -> Dict[str, Any]:
    """Convert command to dictionary for API response."""
    return {
        "command_type": cmd.command_type.value,
        "amount": cmd.amount,
        "target_price": cmd.target_price,
        "raw_text": cmd.raw_text,
        "confidence": cmd.confidence,
        "error_message": cmd.error_message,
    }
