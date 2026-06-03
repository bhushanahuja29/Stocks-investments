from __future__ import annotations

from .symbol_resolver import canonical_crypto_symbol


def tradingview_chart_url(symbol: str, market_type: str) -> str:
    """Build TradingView chart URL for NSE equities or Binance USDT pairs."""
    if market_type in ("indian_stock", "indian_stocks"):
        sym = symbol.upper().strip().replace(".NS", "").replace(".BO", "")
        return f"https://www.tradingview.com/chart/?symbol=NSE:{sym}"
    sym = canonical_crypto_symbol(symbol)
    return f"https://www.tradingview.com/chart/?symbol=BINANCE:{sym}"
