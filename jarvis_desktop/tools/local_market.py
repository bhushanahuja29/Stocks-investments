"""Local fallback when backend /api/market/* is unavailable."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from ..data.nifty50 import NIFTY_50_STOCKS

_BACKEND = Path(__file__).resolve().parents[2] / "crypto_levels_bhushan" / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from indian_quotes import compute_index_movers_by_id  # noqa: E402
from market_helpers import get_crypto_quote_snapshot, get_market_quote  # noqa: E402


def list_nifty50_local() -> dict[str, Any]:
    return {
        "success": True,
        "stocks": NIFTY_50_STOCKS,
        "count": len(NIFTY_50_STOCKS),
        "source": "yahoo_finance",
    }


def compute_index_movers_local(
    index: str,
    min_pct: float,
    period: str = "daily",
    direction: str = "any",
    sort: str = "desc",
) -> dict[str, Any]:
    index_id, label, movers = compute_index_movers_by_id(
        index, min_pct, period=period, direction=direction, sort=sort
    )
    return {
        "success": True,
        "index": index_id,
        "index_label": label,
        "min_pct": min_pct,
        "period": period,
        "direction": direction,
        "sort": sort,
        "movers": movers,
        "count": len(movers),
        "source": "yahoo_finance",
        "data_provider": "yahoo_nse_quote_fields (LTP vs previous close, matches NSE)",
    }


def compute_nifty_movers_local(min_pct: float, period: str = "daily") -> dict[str, Any]:
    return compute_index_movers_local("nifty50", min_pct, period=period, direction="any", sort="desc")


def get_market_quote_local(symbol: str, market_type: str = "crypto") -> dict[str, Any]:
    return get_market_quote(symbol, market_type)
