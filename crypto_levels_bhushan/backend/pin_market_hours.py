"""Trading-session rules for pinned scrip price polling (server-side)."""

from __future__ import annotations

from datetime import datetime, time
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
NSE_OPEN = time(9, 0)
NSE_CLOSE = time(15, 30)

_FOREX_SYMBOLS = frozenset({"XAUUSD", "XAU", "GOLD", "GC=F", "XAU/USD"})


def normalize_pin_market_type(market_type: str) -> str:
    m = (market_type or "").strip().lower()
    if m in ("indian_stock", "indian_stocks"):
        return "indian_stocks"
    if m in ("forex", "commodity"):
        return "forex"
    return "crypto"


def pin_schedule_kind(symbol: str, market_type: str) -> str:
    mtype = normalize_pin_market_type(market_type)
    sym = symbol.upper().strip().replace("/", "")
    if mtype == "indian_stocks":
        return "nse"
    if mtype == "forex" or sym in _FOREX_SYMBOLS:
        return "forex_weekday"
    return "crypto_24_7"


def now_ist() -> datetime:
    return datetime.now(IST)


def is_weekday_ist(dt: datetime | None = None) -> bool:
    dt = dt or now_ist()
    return dt.weekday() < 5


def is_nse_session(dt: datetime | None = None) -> bool:
    dt = dt or now_ist()
    if not is_weekday_ist(dt):
        return False
    t = dt.time()
    return NSE_OPEN <= t <= NSE_CLOSE


def should_poll_pin(symbol: str, market_type: str, dt: datetime | None = None) -> bool:
    kind = pin_schedule_kind(symbol, market_type)
    if kind == "nse":
        return is_nse_session(dt)
    if kind == "forex_weekday":
        return is_weekday_ist(dt)
    return True


def pin_session_status(symbol: str, market_type: str, dt: datetime | None = None) -> str:
    if should_poll_pin(symbol, market_type, dt):
        return ""
    dt = dt or now_ist()
    kind = pin_schedule_kind(symbol, market_type)
    if kind == "nse":
        if not is_weekday_ist(dt):
            return "NSE closed (weekend)"
        if dt.time() < NSE_OPEN:
            return "NSE pre-open"
        return "NSE closed"
    if kind == "forex_weekday":
        return "Gold pause (weekend)"
    return ""
