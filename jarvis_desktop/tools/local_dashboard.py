"""Local fallback for /api/market/dashboard."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_BACKEND = Path(__file__).resolve().parents[2] / "crypto_levels_bhushan" / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from market_dashboard import get_market_dashboard  # noqa: E402


def get_market_dashboard_local() -> dict[str, Any]:
    return get_market_dashboard()
