"""Parse and format 'market updates' voice/text commands."""

from __future__ import annotations

from typing import Any

_UPDATE_CUES = (
    "market update",
    "market updates",
    "market briefing",
    "indices update",
    "index update",
    "market summary",
    "how are markets",
    "how did markets",
    "closing today",
    "moved today",
)


def is_market_updates_query(text: str) -> bool:
    lower = text.lower().strip()
    if any(cue in lower for cue in _UPDATE_CUES):
        return True
    # "tell me nifty bank nifty btc gold"
    hits = sum(
        1
        for kw in ("nifty", "bank nifty", "us100", "us 100", "xau", "gold", "btc", "bitcoin")
        if kw in lower
    )
    if hits >= 2 and any(w in lower for w in ("update", "closing", "moved", "percent", "%", "today")):
        return True
    if lower in ("market updates", "market update", "market updates me", "market update me"):
        return True
    return False


def _fmt_pct(pct: float) -> str:
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct:.2f}%"


def _fmt_price(label: str, row: dict[str, Any]) -> str:
    ltp = row.get("ltp")
    pct = row.get("change_pct")
    prev = row.get("previous_close")
    if ltp is None or pct is None:
        return f"{label}: data unavailable"

    name = row.get("label", label)
    if name in ("Nifty 50", "Bank Nifty"):
        price_s = f"₹{ltp:,.2f}"
        prev_s = f"₹{prev:,.2f}" if prev else "n/a"
    elif row.get("id") == "btc":
        price_s = f"${ltp:,.2f}"
        prev_s = f"${prev:,.2f}" if prev else "n/a"
    elif row.get("id") == "xauusd":
        price_s = f"${ltp:,.2f}"
        prev_s = f"${prev:,.2f}" if prev else "n/a"
    else:
        price_s = f"{ltp:,.2f}"
        prev_s = f"{prev:,.2f}" if prev else "n/a"

    direction = "up" if pct >= 0 else "down"
    return (
        f"{name} at {price_s}, previous close {prev_s}, "
        f"{direction} {_fmt_pct(pct)} today"
    )


def format_market_updates_speech(payload: dict[str, Any]) -> str:
    assets = payload.get("assets") or []
    if not assets:
        return "I could not fetch market updates right now. Check that the backend is running."

    lines = ["Here are your market updates."]
    for row in assets:
        lines.append(_fmt_price(row.get("label", ""), row))
    return " ".join(lines)
