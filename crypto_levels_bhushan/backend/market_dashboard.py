"""Daily snapshot for major indices and key assets (Nifty, Bank Nifty, US100, gold, BTC)."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import yfinance as yf

from indian_quotes import _daily_quote_nse_aligned, change_pct
from market_helpers import get_crypto_quote_snapshot

# Yahoo symbols aligned with NSE / global benchmarks
_YAHOO_INDEX = {
    "nifty50": ("Nifty 50", "^NSEI"),
    "banknifty": ("Bank Nifty", "^NSEBANK"),
    "us100": ("US 100", "^NDX"),
    "xauusd": ("Gold XAUUSD", "GC=F"),
}


def _row_from_yahoo(yahoo_sym: str, label: str, asset_id: str) -> dict[str, Any] | None:
    price, prev, pct = _daily_quote_nse_aligned(yahoo_sym)
    if price is None or prev is None:
        return None
    if pct is None:
        pct = change_pct(price, prev)
    if pct is None:
        return None
    return {
        "id": asset_id,
        "label": label,
        "symbol": yahoo_sym,
        "ltp": round(price, 2),
        "previous_close": round(prev, 2),
        "change_pct": round(pct, 2),
        "change_abs": round(price - prev, 2),
        "market_type": "index" if asset_id != "xauusd" else "commodity",
        "source": "yahoo_finance",
    }


def _row_from_crypto() -> dict[str, Any] | None:
    snap = get_crypto_quote_snapshot("BTCUSDT")
    if not snap:
        return None
    return {
        "id": "btc",
        "label": "Bitcoin BTC",
        "symbol": "BTCUSDT",
        "ltp": snap.get("ltp"),
        "previous_close": snap.get("previous_close"),
        "change_pct": snap.get("change_pct"),
        "change_abs": (
            round(snap["ltp"] - snap["previous_close"], 2)
            if snap.get("ltp") is not None and snap.get("previous_close") is not None
            else None
        ),
        "market_type": "crypto",
        "source": snap.get("source", "delta_exchange"),
    }


def get_market_dashboard() -> dict[str, Any]:
    assets: list[dict[str, Any]] = []

    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {
            pool.submit(_row_from_yahoo, ysym, label, aid): aid
            for aid, (label, ysym) in _YAHOO_INDEX.items()
        }
        futures[pool.submit(_row_from_crypto)] = "btc"

        for fut in as_completed(futures):
            try:
                row = fut.result()
                if row:
                    assets.append(row)
            except Exception:
                continue

    order = ["nifty50", "banknifty", "us100", "xauusd", "btc"]
    assets.sort(key=lambda a: order.index(a["id"]) if a["id"] in order else 99)

    return {
        "success": True,
        "assets": assets,
        "count": len(assets),
        "data_provider": "yahoo_nse_quote_fields_and_delta",
    }
