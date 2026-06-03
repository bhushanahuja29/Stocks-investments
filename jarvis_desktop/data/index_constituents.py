"""Jarvis copy of index constituents — imports backend module when available."""

from __future__ import annotations

import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[2] / "crypto_levels_bhushan" / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from index_constituents import (  # noqa: E402
    BANK_NIFTY_STOCKS,
    FIN_NIFTY_STOCKS,
    INDEX_REGISTRY,
    get_constituents,
    list_indices,
    normalize_index_id,
    resolve_index_from_text,
)

__all__ = [
    "BANK_NIFTY_STOCKS",
    "FIN_NIFTY_STOCKS",
    "INDEX_REGISTRY",
    "get_constituents",
    "list_indices",
    "normalize_index_id",
    "resolve_index_from_text",
]
