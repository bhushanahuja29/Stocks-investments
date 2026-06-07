"""Parse natural-language Indian index mover queries into tool arguments."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .data.index_constituents import resolve_index_from_text


_MOVER_CUES = (
    "moved",
    "move",
    "movers",
    "gainers",
    "losers",
    "percent",
    "%",
    "went up",
    "went down",
    "fell",
    "rise",
    "rose",
    "drop",
    "dropped",
    "change",
    "today",
    "tomorrow",
    "happen",
    "this week",
    "this month",
    "sorted",
    "sort",
    "descending",
    "ascending",
    "highest",
    "lowest",
)


@dataclass
class MoverQuery:
    index: str
    min_pct: float
    period: str
    direction: str
    sort: str
    index_label: str = ""

    def to_tool_args(self) -> dict:
        return {
            "index": self.index,
            "min_pct": self.min_pct,
            "period": self.period,
            "direction": self.direction,
            "sort": self.sort,
        }


def is_mover_query(text: str) -> bool:
    lower = text.lower()
    return any(cue in lower for cue in _MOVER_CUES)


def parse_mover_query(text: str) -> MoverQuery | None:
    if not is_mover_query(text):
        return None

    lower = text.lower()
    index_id, index_label = resolve_index_from_text(text)

    min_pct = 2.0
    pct_match = re.search(r"(-?\d+(?:\.\d+)?)\s*(?:%|percent)", lower)
    if pct_match:
        min_pct = float(pct_match.group(1))
    elif "2 percent" in lower or "2%" in lower:
        min_pct = 2.0
    elif any(w in lower for w in ("tomorrow", "happen", "today")) and "nifty" in lower:
        min_pct = 0.0

    period = "daily"
    if "this month" in lower or "monthly" in lower:
        period = "monthly"
    elif "this week" in lower or "weekly" in lower:
        period = "weekly"

    direction = "any"
    if any(w in lower for w in ("gainers", "went up", "rose", "rising", "up only", "only up")):
        direction = "up"
    elif any(w in lower for w in ("losers", "went down", "fell", "falling", "down only", "only down")):
        direction = "down"

    sort = "desc"
    if any(w in lower for w in ("ascending", "lowest first", "sort asc", "smallest")):
        sort = "asc"
    if "descending" in lower or "highest first" in lower:
        sort = "desc"

    return MoverQuery(
        index=index_id,
        min_pct=min_pct,
        period=period,
        direction=direction,
        sort=sort,
        index_label=index_label,
    )
