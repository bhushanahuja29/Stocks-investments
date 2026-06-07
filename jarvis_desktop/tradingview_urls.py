from __future__ import annotations

from urllib.parse import quote

from .symbol_resolver import canonical_crypto_symbol


def _tv_symbol(symbol: str, market_type: str) -> str:
    if market_type in ("indian_stock", "indian_stocks"):
        sym = symbol.upper().strip().replace(".NS", "").replace(".BO", "")
        return f"NSE:{sym}"
    return f"BINANCE:{canonical_crypto_symbol(symbol)}"


def tradingview_chart_url(
    symbol: str,
    market_type: str,
    *,
    interval: str | None = None,
    layout_id: str | None = None,
) -> str:
    """Build TradingView chart URL for NSE equities or Binance USDT pairs."""
    tv_sym = quote(_tv_symbol(symbol, market_type), safe="")
    base = "https://www.tradingview.com"
    if layout_id:
        path = f"/chart/{layout_id}/"
    else:
        path = "/chart/"
    url = f"{base}{path}?symbol={tv_sym}"
    if interval:
        url += f"&interval={interval}"
    return url
