"""Local fallback when backend /api/market/news is unavailable."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_BACKEND = Path(__file__).resolve().parents[2] / "crypto_levels_bhushan" / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from market_helpers import get_scrip_news  # noqa: E402


def get_scrip_news_local(
    symbol: str,
    market_type: str = "indian_stocks",
    year: int | None = None,
    month: int | None = None,
    limit: int = 30,
    sources: str = "yahoo,moneycontrol",
) -> dict[str, Any]:
    return get_scrip_news(
        symbol,
        market_type=market_type,
        year=year,
        month=month,
        limit=limit,
        sources=sources,
    )
