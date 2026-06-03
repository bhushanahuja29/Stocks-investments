from __future__ import annotations

import calendar
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from .moneycontrol_news import fetch_moneycontrol_news
from .yahoo_news import fetch_yahoo_news

IST = ZoneInfo("Asia/Kolkata")

_MONTH_NAMES = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}


def month_label(year: int, month: int) -> str:
    return f"{calendar.month_name[month]} {year}"


def month_bounds_ist(year: int, month: int) -> tuple[datetime, datetime]:
    start = datetime(year, month, 1, 0, 0, 0, tzinfo=IST)
    if month == 12:
        end = datetime(year + 1, 1, 1, 0, 0, 0, tzinfo=IST)
    else:
        end = datetime(year, month + 1, 1, 0, 0, 0, tzinfo=IST)
    return start, end


def _normalize_title(title: str) -> str:
    t = title.lower()
    t = re.sub(r"[^a-z0-9\s]", "", t)
    return re.sub(r"\s+", " ", t).strip()


def _parse_iso(dt_str: str | None) -> datetime | None:
    if not dt_str:
        return None
    try:
        text = dt_str.replace("Z", "+00:00")
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _in_month(article: dict[str, Any], start: datetime, end: datetime) -> bool:
    dt = _parse_iso(article.get("published_at"))
    if dt is None:
        return True
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=IST)
    local = dt.astimezone(IST)
    return start <= local < end


def _dedupe_articles(
    articles: list[dict[str, Any]],
    prefer_sources: list[str],
) -> list[dict[str, Any]]:
    by_title: dict[str, dict[str, Any]] = {}
    source_rank = {s: i for i, s in enumerate(prefer_sources)}

    for art in articles:
        key = _normalize_title(art.get("title", ""))
        if not key:
            continue
        existing = by_title.get(key)
        if existing is None:
            by_title[key] = art
            continue
        new_rank = source_rank.get(art.get("source", ""), 99)
        old_rank = source_rank.get(existing.get("source", ""), 99)
        if new_rank < old_rank:
            by_title[key] = art
        elif new_rank == old_rank:
            if art.get("published_at") and (not existing.get("published_at") or art["published_at"] > existing["published_at"]):
                by_title[key] = art

    return list(by_title.values())


def fetch_scrip_news(
    symbol: str,
    market_type: str = "indian_stocks",
    year: int | None = None,
    month: int | None = None,
    limit: int = 30,
    sources: tuple[str, ...] = ("yahoo", "moneycontrol"),
) -> dict[str, Any]:
    now = datetime.now(IST)
    year = year or now.year
    month = month or now.month
    sym = symbol.upper().strip().replace(".NS", "")
    mtype = "indian_stocks" if market_type in ("indian_stock", "indian_stocks") else "crypto"

    start, end = month_bounds_ist(year, month)
    warnings: list[str] = [
        "yahoo: only recent headlines available; older months may be incomplete",
    ]

    if datetime(year, month, 1, tzinfo=IST) > now.replace(day=1, hour=0, minute=0, second=0, microsecond=0):
        return {
            "success": True,
            "symbol": sym,
            "market_type": mtype,
            "year": year,
            "month": month,
            "month_label": month_label(year, month),
            "count": 0,
            "articles": [],
            "sources_used": [],
            "warnings": ["requested month is in the future; no articles yet"],
        }

    use_yahoo = "yahoo" in sources
    use_mc = "moneycontrol" in sources and mtype == "indian_stocks"

    collected: list[dict[str, Any]] = []
    sources_used: list[str] = []

    def pull_yahoo() -> list[dict[str, Any]]:
        return fetch_yahoo_news(sym, mtype, limit=40)

    def pull_mc() -> list[dict[str, Any]]:
        return fetch_moneycontrol_news(sym, limit=50)

    futures = {}
    with ThreadPoolExecutor(max_workers=2) as pool:
        if use_mc:
            futures[pool.submit(pull_mc)] = "moneycontrol"
        if use_yahoo:
            futures[pool.submit(pull_yahoo)] = "yahoo_finance"

        for fut in as_completed(futures):
            src = futures[fut]
            try:
                rows = fut.result()
                if rows:
                    sources_used.append(src)
                    collected.extend(rows)
            except Exception:
                if src == "moneycontrol":
                    warnings.append("moneycontrol: fetch failed for this symbol")

    prefer = ["moneycontrol", "yahoo_finance"] if mtype == "indian_stocks" else ["yahoo_finance"]
    filtered = [a for a in collected if _in_month(a, start, end)]
    undated = [a for a in collected if not a.get("published_at")]
    if undated and not filtered:
        filtered = undated[:limit]

    merged = _dedupe_articles(filtered, prefer)
    if not merged and collected:
        dated_outside = [a for a in collected if a.get("published_at") and not _in_month(a, start, end)]
        if dated_outside:
            warnings.append(
                f"no articles in {month_label(year, month)}; "
                f"{len(dated_outside)} headline(s) found in other months (Yahoo recent feed only)"
            )
    merged.sort(key=lambda a: a.get("published_at") or "", reverse=True)
    merged = merged[:limit]

    if mtype == "crypto" and "moneycontrol" in sources:
        warnings.append("moneycontrol: Indian equities only; crypto uses Yahoo Finance")

    return {
        "success": True,
        "symbol": sym,
        "market_type": mtype,
        "year": year,
        "month": month,
        "month_label": month_label(year, month),
        "count": len(merged),
        "articles": merged,
        "sources_used": sources_used,
        "warnings": warnings,
    }
