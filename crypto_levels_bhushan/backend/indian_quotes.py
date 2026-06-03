"""
Indian NSE equity quotes — aligned with NSE/Google "today vs previous close".

Daily: Yahoo Finance quote fields (regularMarketPrice / regularMarketPreviousClose).
Weekly / monthly: last two valid OHLC closes on 1wk / 1mo intervals.
"""

from __future__ import annotations

import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import yfinance as yf

from index_constituents import get_constituents, normalize_index_id

_INTERVAL_MAP = {
    "weekly": ("1wk", "1y"),
    "monthly": ("1mo", "5y"),
}


def nse_yahoo_symbol(symbol: str) -> str:
    upper = symbol.upper().strip()
    if ".NS" in upper or ".BO" in upper:
        return upper
    return f"{upper}.NS"


def _finite(value: Any) -> float | None:
    try:
        v = float(value)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def change_pct(last: float, prev: float) -> float | None:
    if prev == 0 or last == 0:
        return None
    pct = ((last - prev) / prev) * 100.0
    return pct if math.isfinite(pct) else None


def _daily_quote_nse_aligned(ysym: str) -> tuple[float | None, float | None, float | None]:
    try:
        info = yf.Ticker(ysym).info
    except Exception:
        return None, None, None

    price = _finite(info.get("regularMarketPrice") or info.get("currentPrice"))
    prev = _finite(info.get("regularMarketPreviousClose") or info.get("previousClose"))
    pct = _finite(info.get("regularMarketChangePercent"))

    if price is None or prev is None:
        return None, None, None

    if pct is None:
        pct = change_pct(price, prev)

    return price, prev, pct


def get_symbol_quote_snapshot(symbol: str) -> dict[str, Any] | None:
    """Single NSE equity quote for pin widget / market quote API."""
    ysym = nse_yahoo_symbol(symbol)
    sym = symbol.upper().strip().replace(".NS", "").replace(".BO", "")
    try:
        info = yf.Ticker(ysym).info
    except Exception:
        return None

    ltp = _finite(info.get("regularMarketPrice") or info.get("currentPrice"))
    open_p = _finite(info.get("regularMarketOpen") or info.get("open"))
    prev = _finite(info.get("regularMarketPreviousClose") or info.get("previousClose"))
    pct = _finite(info.get("regularMarketChangePercent"))

    if ltp is None or prev is None:
        return None
    if pct is None:
        pct = change_pct(ltp, prev)
    if pct is None:
        return None

    return {
        "success": True,
        "symbol": sym,
        "market_type": "indian_stocks",
        "ltp": round(ltp, 2),
        "open": round(open_p, 2) if open_p is not None else None,
        "previous_close": round(prev, 2),
        "change_pct": round(pct, 2),
        "change_inr": round(ltp - prev, 2),
        "source": "yahoo_finance",
    }


def _period_change_from_history(ysym: str, period: str) -> tuple[float | None, float | None, float | None]:
    interval, yf_period = _INTERVAL_MAP.get(period, _INTERVAL_MAP["weekly"])
    try:
        hist = yf.Ticker(ysym).history(period=yf_period, interval=interval, auto_adjust=True)
    except Exception:
        return None, None, None

    if hist is None or hist.empty or "Close" not in hist.columns:
        return None, None, None

    closes = hist["Close"].dropna()
    if len(closes) < 2:
        return None, None, None

    prev_close = float(closes.iloc[-2])
    last_close = float(closes.iloc[-1])
    pct = change_pct(last_close, prev_close)
    if pct is None:
        return None, None, None
    return last_close, prev_close, pct


def _passes_direction(pct: float, min_pct: float, direction: str) -> bool:
    direction = direction if direction in ("up", "down", "any") else "any"
    if direction == "up":
        return pct >= min_pct
    if direction == "down":
        return pct <= -min_pct
    return abs(pct) >= min_pct


def _fetch_one_mover(
    item: dict[str, str],
    min_pct: float,
    period: str,
    direction: str,
    index_id: str,
    index_label: str,
) -> dict[str, Any] | None:
    sym = item["symbol"]
    ysym = nse_yahoo_symbol(sym)

    if period == "daily":
        price, prev_close, pct = _daily_quote_nse_aligned(ysym)
    else:
        price, prev_close, pct = _period_change_from_history(ysym, period)

    if pct is None or price is None or not _passes_direction(pct, min_pct, direction):
        return None

    change_inr = round(price - prev_close, 2) if prev_close is not None else None

    return {
        "symbol": sym,
        "name": item["name"],
        "price": round(price, 2),
        "previous_close": round(prev_close, 2) if prev_close is not None else None,
        "change_inr": change_inr,
        "change_pct": round(pct, 2),
        "market_type": "indian_stock",
        "period": period,
        "direction_filter": direction,
        "index": index_id,
        "index_label": index_label,
        "yahoo_symbol": ysym,
        "data_source": "yahoo_quote_fields" if period == "daily" else "yahoo_history",
    }


def compute_index_movers(
    constituents: list[dict[str, str]],
    min_pct: float,
    period: str = "daily",
    direction: str = "any",
    sort: str = "desc",
    index_id: str = "nifty50",
    index_label: str = "Nifty 50",
) -> list[dict[str, Any]]:
    period = period if period in ("daily", "weekly", "monthly") else "daily"
    direction = direction if direction in ("up", "down", "any") else "any"
    sort = sort if sort in ("desc", "asc") else "desc"

    movers: list[dict[str, Any]] = []

    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = {
            pool.submit(
                _fetch_one_mover, item, min_pct, period, direction, index_id, index_label
            ): item
            for item in constituents
        }
        for future in as_completed(futures):
            try:
                row = future.result()
                if row:
                    movers.append(row)
            except Exception:
                continue

    reverse = sort == "desc"
    movers.sort(key=lambda m: float(m["change_pct"]), reverse=reverse)
    return movers


def compute_index_movers_by_id(
    index: str,
    min_pct: float,
    period: str = "daily",
    direction: str = "any",
    sort: str = "desc",
) -> tuple[str, str, list[dict[str, Any]]]:
    index_id, label, constituents = get_constituents(index)
    movers = compute_index_movers(
        constituents,
        min_pct,
        period=period,
        direction=direction,
        sort=sort,
        index_id=index_id,
        index_label=label,
    )
    return index_id, label, movers


def compute_nifty_movers_yfinance(min_pct: float, period: str = "daily") -> list[dict[str, Any]]:
    """Backward-compatible alias — Nifty 50, any direction, sorted by magnitude desc."""
    _, _, movers = compute_index_movers_by_id(
        "nifty50", min_pct, period=period, direction="any", sort="desc"
    )
    return movers
