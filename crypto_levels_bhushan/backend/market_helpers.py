"""Market scan helpers for Krypto agent API routes."""

from __future__ import annotations

import time
from typing import Any

import math

import requests

from indian_quotes import (
    _daily_quote_nse_aligned,
    _period_change_from_history,
    compute_index_movers_by_id,
    compute_nifty_movers_yfinance,
    get_symbol_quote_snapshot,
    nse_yahoo_symbol,
)
from index_constituents import list_indices
from v3 import delta_get, fnum

_CACHE: dict[str, tuple[float, Any]] = {}
_CACHE_TTL_SEC = 60


def _cache_get(key: str) -> Any | None:
    entry = _CACHE.get(key)
    if not entry:
        return None
    ts, value = entry
    if time.time() - ts > _CACHE_TTL_SEC:
        return None
    return value


def _cache_set(key: str, value: Any) -> None:
    _CACHE[key] = (time.time(), value)


def _change_pct(last: float, prev: float) -> float | None:
    if prev == 0 or last == 0:
        return None
    pct = ((last - prev) / prev) * 100.0
    return pct if math.isfinite(pct) else None


def _valid_pct(pct: float | None) -> bool:
    return pct is not None and math.isfinite(pct)


def fetch_delta_candles_short(symbol: str, resolution: str = "1d", weeks_back: int = 21) -> list[dict[str, Any]]:
    end = int(time.time())
    start = end - weeks_back * 7 * 24 * 3600
    params = {"resolution": resolution, "symbol": symbol.upper(), "start": start, "end": end}
    data = delta_get("/v2/history/candles", params)
    if not isinstance(data, dict) or "result" not in data:
        return []
    candles = []
    for item in data["result"]:
        candles.append(
            {
                "time": item["time"],
                "close": fnum(item["close"]),
            }
        )
    candles.sort(key=lambda x: x["time"])
    return candles


def fetch_delta_tickers_map() -> dict[str, dict[str, Any]]:
    cached = _cache_get("delta_tickers")
    if cached is not None:
        return cached
    out: dict[str, dict[str, Any]] = {}
    try:
        response = requests.get(
            "https://api.delta.exchange/v2/tickers",
            timeout=15,
            headers={"Accept": "application/json"},
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                for ticker in data.get("result", []):
                    sym = str(ticker.get("symbol", "")).upper()
                    if sym:
                        out[sym] = ticker
    except requests.RequestException:
        pass
    _cache_set("delta_tickers", out)
    return out


def crypto_daily_change_pct(symbol: str, tickers: dict[str, dict[str, Any]]) -> tuple[float | None, float | None]:
    upper = symbol.upper()
    ticker = tickers.get(upper)
    if ticker:
        mark = ticker.get("mark_price") or ticker.get("close")
        if mark is not None:
            last = float(mark)
            open_price = ticker.get("open") or ticker.get("day_open")
            quotes = ticker.get("quotes")
            if isinstance(quotes, dict) and quotes.get("open"):
                open_price = quotes.get("open")
            ohlc = ticker.get("ohlc")
            if isinstance(ohlc, dict) and ohlc.get("open"):
                open_price = ohlc.get("open")
            if open_price is not None:
                pct = _change_pct(last, float(open_price))
                if pct is not None:
                    return last, pct

    try:
        candles = fetch_delta_candles_short(upper, "1d", weeks_back=21)
        if len(candles) < 2:
            return None, None
        prev_close = float(candles[-2]["close"])
        last_close = float(candles[-1]["close"])
        return last_close, _change_pct(last_close, prev_close)
    except Exception:
        return None, None


def indian_stock_daily_change_pct(symbol: str, period: str = "daily") -> tuple[float | None, float | None]:
    formatted = nse_yahoo_symbol(symbol)
    if period == "daily":
        price, _prev, pct = _daily_quote_nse_aligned(formatted)
        return price, pct
    price, _prev, pct = _period_change_from_history(formatted, period)
    return price, pct


def compute_index_movers(
    index: str,
    min_pct: float,
    period: str = "daily",
    direction: str = "any",
    sort: str = "desc",
) -> dict[str, Any]:
    cache_key = f"index_movers_{index}_{min_pct}_{period}_{direction}_{sort}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    index_id, label, movers = compute_index_movers_by_id(
        index, min_pct, period=period, direction=direction, sort=sort
    )
    payload = {
        "success": True,
        "index": index_id,
        "index_label": label,
        "min_pct": min_pct,
        "period": period,
        "direction": direction,
        "sort": sort,
        "movers": movers,
        "count": len(movers),
        "data_provider": "yahoo_nse_quote_fields",
    }
    _cache_set(cache_key, payload)
    return payload


def compute_nifty_movers(min_pct: float, period: str = "daily") -> list[dict[str, Any]]:
    payload = compute_index_movers("nifty50", min_pct, period=period, direction="any", sort="desc")
    return payload["movers"]


def _yahoo_crypto_yf_symbol(delta_symbol: str) -> str:
    upper = delta_symbol.upper().strip()
    if upper.endswith("USDT"):
        return f"{upper[:-4]}-USD"
    if upper.endswith("USD") and not upper.endswith("USDT"):
        return f"{upper[:-3]}-USD"
    return f"{upper}-USD"


def get_crypto_quote_snapshot(symbol: str) -> dict[str, Any] | None:
    """Crypto quote snapshot (Delta mark + day open; prev close from candles or Yahoo)."""
    upper = symbol.upper().strip()
    tickers = fetch_delta_tickers_map()
    ticker = tickers.get(upper)

    ltp: float | None = None
    open_p: float | None = None
    prev: float | None = None

    if ticker:
        mark = ticker.get("mark_price") or ticker.get("close")
        if mark is not None:
            ltp = float(mark)
        ohlc = ticker.get("ohlc")
        if isinstance(ohlc, dict) and ohlc.get("open") is not None:
            open_p = float(ohlc["open"])
        quotes = ticker.get("quotes")
        if isinstance(quotes, dict) and quotes.get("open") is not None:
            open_p = open_p or float(quotes["open"])
        if open_p is None:
            open_p = ticker.get("open") or ticker.get("day_open")
            if open_p is not None:
                open_p = float(open_p)

    try:
        candles = fetch_delta_candles_short(upper, "1d", weeks_back=21)
        if len(candles) >= 2:
            prev = float(candles[-2]["close"])
            if ltp is None:
                ltp = float(candles[-1]["close"])
    except Exception:
        pass

    if ltp is None or prev is None:
        try:
            import yfinance as yf

            yf_sym = _yahoo_crypto_yf_symbol(upper)
            info = yf.Ticker(yf_sym).info
            if ltp is None:
                ltp = _finite(info.get("regularMarketPrice") or info.get("currentPrice"))
            if open_p is None:
                open_p = _finite(info.get("regularMarketOpen") or info.get("open"))
            if prev is None:
                prev = _finite(info.get("regularMarketPreviousClose") or info.get("previousClose"))
        except Exception:
            pass

    if ltp is None or prev is None:
        return None

    pct = _change_pct(ltp, prev)
    if pct is None:
        return None

    return {
        "success": True,
        "symbol": upper,
        "market_type": "crypto",
        "ltp": round(ltp, 2),
        "open": round(open_p, 2) if open_p is not None else None,
        "previous_close": round(prev, 2),
        "change_pct": round(pct, 2),
        "change_inr": None,
        "source": "delta_exchange",
    }


def _finite(value: Any) -> float | None:
    try:
        v = float(value)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None


_NEWS_CACHE: dict[str, tuple[float, Any]] = {}
_NEWS_CACHE_TTL_SEC = 600


def get_scrip_news(
    symbol: str,
    market_type: str = "indian_stocks",
    year: int | None = None,
    month: int | None = None,
    limit: int = 30,
    sources: str = "yahoo,moneycontrol",
) -> dict[str, Any]:
    from news.aggregator import fetch_scrip_news

    src_tuple = tuple(s.strip() for s in sources.split(",") if s.strip())
    cache_key = f"news_{symbol}_{market_type}_{year}_{month}_{sources}_{limit}"
    ent = _NEWS_CACHE.get(cache_key)
    if ent and time.time() - ent[0] <= _NEWS_CACHE_TTL_SEC:
        return ent[1]

    payload = fetch_scrip_news(
        symbol,
        market_type=market_type,
        year=year,
        month=month,
        limit=limit,
        sources=src_tuple or ("yahoo", "moneycontrol"),
    )
    _NEWS_CACHE[cache_key] = (time.time(), payload)
    return payload


def get_market_quote(symbol: str, market_type: str = "crypto") -> dict[str, Any]:
    """Quote snapshot for pin overlay and GET /api/market/quote."""
    if market_type in ("indian_stock", "indian_stocks"):
        snap = get_symbol_quote_snapshot(symbol)
        if snap:
            return snap
        raise ValueError(f"No quote data for {symbol}")

    if market_type in ("forex", "commodity"):
        sym = symbol.upper().strip()
        yahoo_sym = "GC=F" if sym in ("XAUUSD", "XAU", "GOLD", "XAU/USD") else sym
        try:
            import yfinance as yf

            ticker = yf.Ticker(yahoo_sym)
            hist = ticker.history(period="5d")
            if hist is None or hist.empty:
                raise ValueError(f"No forex quote for {symbol}")
            last = float(hist["Close"].iloc[-1])
            prev = float(hist["Close"].iloc[-2]) if len(hist) > 1 else last
            pct = ((last - prev) / prev * 100) if prev else 0.0
            return {
                "symbol": sym,
                "market_type": "forex",
                "ltp": round(last, 2),
                "open": round(float(hist["Open"].iloc[-1]), 2),
                "previous_close": round(prev, 2),
                "change_pct": round(pct, 2),
                "change_inr": None,
                "source": "yahoo_finance",
            }
        except Exception as exc:
            raise ValueError(f"No quote data for {symbol}: {exc}") from exc

    snap = get_crypto_quote_snapshot(symbol)
    if snap:
        return snap
    raise ValueError(f"No quote data for {symbol}")


def compute_watchlist_movers(coll, min_pct: float, market_type: str | None = None) -> list[dict[str, Any]]:
    cache_key = f"watchlist_movers_{min_pct}_{market_type or 'all'}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    scrips = list(coll.find({"active": True, "monitoring_type": "multi_level"}))
    delta_tickers = fetch_delta_tickers_map()
    movers: list[dict[str, Any]] = []

    for scrip in scrips:
        symbol = scrip.get("symbol")
        if not symbol:
            continue
        mtype = scrip.get("market_type", "crypto")
        if market_type and market_type not in ("all", mtype):
            if market_type == "crypto" and mtype != "crypto":
                continue
            if market_type in ("indian_stock", "indian_stocks") and mtype not in (
                "indian_stock",
                "indian_stocks",
            ):
                continue

        last: float | None = None
        pct: float | None = None
        if mtype in ("indian_stock", "indian_stocks"):
            last, pct = indian_stock_daily_change_pct(str(symbol))
        elif mtype == "crypto":
            last, pct = crypto_daily_change_pct(str(symbol), delta_tickers)
        else:
            continue

        if not _valid_pct(pct):
            continue
        if abs(pct) >= min_pct:
            movers.append(
                {
                    "symbol": symbol,
                    "price": round(float(last), 2) if last is not None else None,
                    "change_pct": round(float(pct), 2),
                    "market_type": mtype,
                }
            )

    movers.sort(key=lambda m: abs(m["change_pct"]), reverse=True)
    _cache_set(cache_key, movers)
    return movers
