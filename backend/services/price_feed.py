"""
NexaVault – Price Feed Service
================================
Fetches the current ALGO/USD price from:
  1. CoinGecko public API  (primary)
  2. Mock / static fallback (when API is unavailable – testnet / CI)

All prices are returned in USD cents × 1000 (i.e. integer micro-dollars)
so they can be passed directly to the smart contract without floats.
Example: $0.175 ALGO  →  175_000

Usage:
    from backend.services.price_feed import get_algo_price
    price = await get_algo_price()
"""

import logging
import os
import time
from typing import Optional

import httpx                      # async HTTP client

logger = logging.getLogger("nexavault.price_feed")

# ── Config ────────────────────────────────────────────────────────────────────
COINGECKO_URL = (
    "https://api.coingecko.com/api/v3/simple/price"
    "?ids=algorand&vs_currencies=usd"
)
HTTP_TIMEOUT   = 5.0   # seconds
MOCK_PRICE_USD = 0.175  # fallback mock price in USD
USE_MOCK       = os.getenv("USE_MOCK_PRICE", "false").lower() == "true"

# Simple in-memory cache to avoid hammering the API
_cache: dict = {"price": None, "ts": 0.0}
CACHE_TTL = 30  # seconds


def _usd_to_contract_int(usd: float) -> int:
    """Convert a float USD price to the integer representation used on-chain.

    Contract stores price as  USD × 1_000_000  (6 decimal places),
    matching the convention used for USDC amounts (micro-USDC).

    Args:
        usd: Price in USD, e.g. 0.175

    Returns:
        Integer, e.g. 175_000
    """
    return int(usd * 1_000_000)


async def _fetch_from_coingecko() -> Optional[float]:
    """Hit CoinGecko for the live ALGO/USD spot price.

    Returns:
        Price as float USD, or None on error.
    """
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            resp = await client.get(COINGECKO_URL)
            resp.raise_for_status()
            data  = resp.json()
            price = data["algorand"]["usd"]
            logger.info("CoinGecko price fetched: $%.6f ALGO/USD", price)
            return float(price)
    except httpx.HTTPStatusError as exc:
        logger.warning("CoinGecko HTTP error: %s", exc)
    except httpx.RequestError as exc:
        logger.warning("CoinGecko request error: %s", exc)
    except (KeyError, ValueError) as exc:
        logger.warning("CoinGecko parse error: %s", exc)
    return None


def _mock_price() -> float:
    """Return a static mock price for local / testnet development.

    Simulates minor price fluctuation using a sine-like pattern based on time
    so the AI agent can observe price changes without a live API.
    """
    import math
    t     = time.time()
    swing = 0.02 * math.sin(t / 60)          # ±$0.02 oscillation per minute
    price = MOCK_PRICE_USD + swing
    logger.debug("Mock price: $%.6f", price)
    return price


async def get_algo_price() -> dict:
    """Fetch the current ALGO/USD price.

    Returns a dict with:
        {
            "price_usd"      : float  – raw USD price
            "price_contract" : int    – on-chain integer (USD × 1_000_000)
            "source"         : str    – "coingecko" | "mock"
        }
    """
    global _cache

    # Return cached value if still fresh
    if _cache["price"] is not None and (time.time() - _cache["ts"]) < CACHE_TTL:
        logger.debug("Returning cached price")
        return _cache["price"]

    if USE_MOCK:
        usd = _mock_price()
        source = "mock"
    else:
        usd = await _fetch_from_coingecko()
        if usd is None:
            logger.warning("Falling back to mock price")
            usd    = _mock_price()
            source = "mock_fallback"
        else:
            source = "coingecko"

    result = {
        "price_usd"      : round(usd, 8),
        "price_contract" : _usd_to_contract_int(usd),
        "source"         : source,
    }

    # Cache it
    _cache = {"price": result, "ts": time.time()}
    logger.info("Price result: %s", result)
    return result
