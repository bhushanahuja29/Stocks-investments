from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import yfinance as yf

from indian_quotes import nse_yahoo_symbol


def _yahoo_crypto_yf_symbol(delta_symbol: str) -> str:
    upper = delta_symbol.upper().strip()
    if upper.endswith("USDT"):
        return f"{upper[:-4]}-USD"
    if upper.endswith("USD") and not upper.endswith("USDT"):
        return f"{upper[:-3]}-USD"
    return f"{upper}-USD"


def _parse_pub_date(raw: Any) -> datetime | None:
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        try:
            ts = float(raw)
            if ts > 1e12:
                ts /= 1000.0
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        except (OSError, ValueError, OverflowError):
            return None
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return None
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            pass
        for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                dt = datetime.strptime(text[:19], fmt[: len(text)])
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                continue
    return None


def _extract_article(item: dict[str, Any]) -> dict[str, Any] | None:
    content = item.get("content") if isinstance(item.get("content"), dict) else {}
    title = (
        item.get("title")
        or content.get("title")
        or item.get("headline")
    )
    if not title or not str(title).strip():
        return None

    url = (
        item.get("link")
        or item.get("url")
        or content.get("canonicalUrl")
        or content.get("clickThroughUrl")
    )
    if isinstance(url, dict):
        url = url.get("url") or url.get("href")
    if not url:
        return None

    pub = (
        content.get("pubDate")
        or content.get("displayTime")
        or item.get("providerPublishTime")
        or item.get("pubDate")
    )
    dt = _parse_pub_date(pub)

    publisher = (
        item.get("publisher")
        or (content.get("provider") or {}).get("displayName")
        if isinstance(content.get("provider"), dict)
        else content.get("provider")
    )
    summary = content.get("summary") or content.get("description") or item.get("summary")

    return {
        "title": str(title).strip(),
        "url": str(url).strip(),
        "source": "yahoo_finance",
        "publisher": str(publisher).strip() if publisher else None,
        "published_at": dt.isoformat() if dt else None,
        "summary": str(summary).strip()[:500] if summary else None,
    }


def yahoo_symbol(symbol: str, market_type: str) -> str:
    if market_type in ("indian_stock", "indian_stocks"):
        return nse_yahoo_symbol(symbol)
    return _yahoo_crypto_yf_symbol(symbol.upper().strip())


def fetch_yahoo_news(
    symbol: str,
    market_type: str = "indian_stocks",
    limit: int = 40,
) -> list[dict[str, Any]]:
    ysym = yahoo_symbol(symbol, market_type)
    try:
        ticker = yf.Ticker(ysym)
        raw: list[Any] = []
        if hasattr(ticker, "get_news"):
            try:
                raw = ticker.get_news(count=limit) or []
            except TypeError:
                raw = ticker.get_news(count=limit, tab="news") or []
        if not raw:
            raw = getattr(ticker, "news", None) or []
    except Exception:
        return []

    articles: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    for item in raw[:limit]:
        if not isinstance(item, dict):
            continue
        row = _extract_article(item)
        if not row or row["url"] in seen_urls:
            continue
        seen_urls.add(row["url"])
        articles.append(row)
    return articles
