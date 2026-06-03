"""Parse natural-language stock news queries (symbol + month/year)."""

from __future__ import annotations

import calendar
import re
from dataclasses import dataclass
from datetime import datetime

_NEWS_CUES = (
    "news",
    "headlines",
    "headline",
    "articles",
    "article",
    "latest news",
    "stock news",
)

_MONTH_MAP = {
    "january": 1,
    "jan": 1,
    "february": 2,
    "feb": 2,
    "march": 3,
    "mar": 3,
    "april": 4,
    "apr": 4,
    "may": 5,
    "june": 6,
    "jun": 6,
    "july": 7,
    "jul": 7,
    "august": 8,
    "aug": 8,
    "september": 9,
    "sep": 9,
    "sept": 9,
    "october": 10,
    "oct": 10,
    "november": 11,
    "nov": 11,
    "december": 12,
    "dec": 12,
}


@dataclass
class NewsQuery:
    symbol_text: str
    year: int
    month: int
    limit: int = 30

    def to_api_kwargs(self, symbol: str, market_type: str) -> dict:
        return {
            "symbol": symbol,
            "market_type": market_type,
            "year": self.year,
            "month": self.month,
            "limit": self.limit,
        }


def is_news_query(text: str) -> bool:
    lower = text.lower()
    return any(cue in lower for cue in _NEWS_CUES)


def _parse_month_year(text: str) -> tuple[int | None, int | None]:
    lower = text.lower()
    now = datetime.now()
    year: int | None = None
    month: int | None = None

    ym = re.search(r"\b(\d{1,2})\s*/\s*(\d{4})\b", lower)
    if ym:
        month, year = int(ym.group(1)), int(ym.group(2))
        return month, year

    ym2 = re.search(r"\b(\d{4})\s*[-/]\s*(\d{1,2})\b", lower)
    if ym2:
        year, month = int(ym2.group(1)), int(ym2.group(2))
        return month, year

    for name, num in _MONTH_MAP.items():
        if re.search(rf"\b{name}\b", lower):
            month = num
            break

    ymatch = re.search(r"\b(20\d{2})\b", lower)
    if ymatch:
        year = int(ymatch.group(1))

    if month and not year:
        year = now.year
    return month, year


def _strip_news_phrases(text: str) -> str:
    t = text
    patterns = [
        r"\b(get|show|give|fetch|find|tell)\s+me\b",
        r"\b(get|show|give|fetch|find)\b",
        r"\bnews\s+of\b",
        r"\bnews\s+for\b",
        r"\bnews\s+about\b",
        r"\bheadlines\s+(of|for|about)\b",
        r"\barticles\s+(of|for|about)\b",
        r"\blatest\s+news\b",
        r"\bstock\s+news\b",
        r"\bnews\b",
        r"\bheadlines\b",
        r"\barticles\b",
    ]
    for pat in patterns:
        t = re.sub(pat, " ", t, flags=re.IGNORECASE)
    for name in _MONTH_MAP:
        t = re.sub(rf"\b{name}\b", " ", t, flags=re.IGNORECASE)
    t = re.sub(r"\b20\d{2}\b", " ", t)
    t = re.sub(r"\b\d{1,2}\s*/\s*\d{4}\b", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def parse_news_query(text: str) -> NewsQuery | None:
    if not is_news_query(text):
        return None

    month, year = _parse_month_year(text)
    now = datetime.now()
    if month is None:
        month = now.month
    if year is None:
        year = now.year

    symbol_text = _strip_news_phrases(text)
    if not symbol_text or len(symbol_text) < 2:
        symbol_text = text

    return NewsQuery(symbol_text=symbol_text, year=year, month=month)
