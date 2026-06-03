"""Persist pinned scrips to a local JSON file."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .quote_service import normalize_market_type

@dataclass
class PinnedEntry:
    symbol: str
    market_type: str

    def key(self) -> str:
        return self.symbol.upper().strip()


def pin_store_path() -> Path:
    path = Path(__file__).resolve().parent / "data" / "pinned_scrips.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def load_pins(path: Path | None = None) -> list[PinnedEntry]:
    p = path or pin_store_path()
    if not p.is_file():
        return []
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(raw, list):
        return []
    out: list[PinnedEntry] = []
    seen: set[str] = set()
    for item in raw:
        if not isinstance(item, dict):
            continue
        sym = str(item.get("symbol", "")).upper().strip()
        if not sym or sym in seen:
            continue
        mtype = normalize_market_type(str(item.get("market_type", "indian_stocks")))
        seen.add(sym)
        out.append(PinnedEntry(symbol=sym, market_type=mtype))
    return out


def save_pins(entries: list[PinnedEntry], path: Path | None = None) -> None:
    p = path or pin_store_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = [asdict(e) for e in entries]
    p.write_text(json.dumps(payload, indent=2), encoding="utf-8")
