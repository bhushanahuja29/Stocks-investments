from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class JarvisResponse:
    text: str
    payload: dict[str, Any] = field(default_factory=dict)
    log_detail: str | None = None


@dataclass
class LevelDistance:
    trigger_price: float
    current_price: float
    distance_pct: float
    symbol: str
    timeframe: str | None = None
    market_type: str | None = None
