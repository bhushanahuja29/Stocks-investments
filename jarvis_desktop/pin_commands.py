from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class PinCommand:
    action: str  # "pin" | "unpin" | "unpin_all"
    symbol_text: str | None = None


_UNPIN_ALL = re.compile(
    r"\b(?:unpin\s+all|unpin\s+everything|clear\s+all\s+pins|remove\s+all\s+pins)\b",
    re.IGNORECASE,
)
_UNPIN_ONE = re.compile(
    r"\b(?:unpin|unstick|remove\s+pin|close\s+pin)\s+(\S.+)$",
    re.IGNORECASE,
)
_UNPIN = re.compile(
    r"\b(?:unpin|unstick|remove\s+pin|close\s+pin|stop\s+pinning)\b",
    re.IGNORECASE,
)
_PIN_TAIL = re.compile(
    r"\b(?:pin|stick)\s+(.+?)(?:\s+on\s+(?:the\s+)?(?:screen|side))?\s*$",
    re.IGNORECASE,
)
_WATCH_SCREEN = re.compile(
    r"\bwatch\s+(.+?)\s+on\s+(?:the\s+)?(?:screen|side)\s*$",
    re.IGNORECASE,
)
_PIN_BARE = re.compile(r"\b(?:pin|stick)\s+(\S.+)$", re.IGNORECASE)


def parse_pin_command(text: str) -> PinCommand | None:
    """Parse pin / unpin voice or typed commands."""
    raw = text.strip()
    if not raw:
        return None
    if _UNPIN_ALL.search(raw):
        return PinCommand(action="unpin_all")
    m = _UNPIN_ONE.search(raw)
    if m:
        tail = m.group(1).strip()
        if tail.lower() not in ("all", "everything"):
            return PinCommand(action="unpin", symbol_text=tail)
    if _UNPIN.search(raw):
        return PinCommand(action="unpin")

    m = _PIN_TAIL.search(raw)
    if m:
        tail = m.group(1).strip()
        if tail and not _looks_like_noise(tail):
            return PinCommand(action="pin", symbol_text=tail)

    m = _WATCH_SCREEN.search(raw)
    if m:
        tail = m.group(1).strip()
        if tail:
            return PinCommand(action="pin", symbol_text=tail)

    m = _PIN_BARE.search(raw)
    if m:
        tail = m.group(1).strip()
        if tail and not _looks_like_noise(tail):
            return PinCommand(action="pin", symbol_text=tail)

    return None


def _looks_like_noise(tail: str) -> bool:
    lower = tail.lower()
    return lower in ("it", "this", "that", "stock", "symbol")


def format_pin_confirmation(quote: dict) -> str:
    sym = quote.get("symbol", "")
    ltp = quote.get("ltp")
    pct = quote.get("change_pct")
    if ltp is not None and pct is not None:
        sign = "+" if pct >= 0 else ""
        return f"Pinned {sym} at {ltp}, {sign}{pct} percent versus previous close."
    if ltp is not None:
        return f"Pinned {sym} at {ltp}."
    return f"Pinned {sym} to the right side of your screen."
