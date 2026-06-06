from __future__ import annotations

from typing import Any

import requests

from .backend_client import BackendClient
from .tools import local_market


def normalize_market_type(market_type: str) -> str:
    m = (market_type or "").strip().lower()
    if m in ("indian_stock", "indian_stocks"):
        return "indian_stocks"
    if m in ("forex", "commodity"):
        return "forex"
    return "crypto"


def fetch_market_quote(
    backend: BackendClient,
    symbol: str,
    market_type: str,
) -> dict[str, Any]:
    """Backend quote with local yfinance/Delta fallback."""
    mtype = normalize_market_type(market_type)
    try:
        return backend.get_market_quote(symbol, mtype)
    except requests.RequestException:
        return local_market.get_market_quote_local(symbol, mtype)
