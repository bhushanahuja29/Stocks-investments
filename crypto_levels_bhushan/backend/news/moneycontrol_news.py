from __future__ import annotations

import re
import time
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

try:
    from curl_cffi import requests as _cffi_requests

    _HAS_CURL_CFFI = True
except ImportError:
    _HAS_CURL_CFFI = False
from dateutil import parser as date_parser

from .mc_symbol_map import get_static_slug

IST = ZoneInfo("Asia/Kolkata")

_MC_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/json",
    "Accept-Language": "en-IN,en;q=0.9",
}

_SLUG_CACHE: dict[str, tuple[float, str]] = {}
_SLUG_TTL = 86400

_DATE_PATTERNS = [
    re.compile(
        r"\b(\d{1,2})[-/](\d{1,2})[-/](\d{4})\b",
    ),
    re.compile(
        r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{1,2})\s+(\d{4})\b",
        re.IGNORECASE,
    ),
]


def _cache_get_slug(symbol: str) -> str | None:
    key = symbol.upper()
    entry = _SLUG_CACHE.get(key)
    if not entry:
        return None
    ts, slug = entry
    if time.time() - ts > _SLUG_TTL:
        return None
    return slug


def _cache_set_slug(symbol: str, slug: str) -> None:
    _SLUG_CACHE[symbol.upper()] = (time.time(), slug)


def resolve_moneycontrol_slug(nse_symbol: str) -> str | None:
    sym = nse_symbol.upper().strip().replace(".NS", "")
    cached = _cache_get_slug(sym)
    if cached:
        return cached

    static = get_static_slug(sym)
    if static:
        _cache_set_slug(sym, static)
        return static

    slug = _slug_from_autosuggest(sym)
    if slug:
        _cache_set_slug(sym, slug)
        return slug

    return None


def _slug_from_autosuggest(symbol: str) -> str | None:
    url = "https://www.moneycontrol.com/mccode/common/autosuggestion_solr.php"
    try:
        resp = _http_get(
            url,
            params={"classic": "true", "query": symbol, "type": "1"},
        )
        if resp is None or resp.status_code != 200:
            return None
        data = resp.json()
    except Exception:
        return None

    items = data if isinstance(data, list) else data.get("result") or data.get("data") or []
    for item in items:
        if not isinstance(item, dict):
            continue
        nse = str(item.get("nseid") or item.get("NSEID") or item.get("sc_nseid") or "").upper()
        if nse and nse != symbol.upper():
            continue
        slug = (
            item.get("sc_slug")
            or item.get("sc_id")
            or item.get("slug")
            or item.get("sc_comp")
        )
        if slug:
            return str(slug).lower().replace(" ", "")
        link = item.get("link") or item.get("url") or ""
        if "stockpricequote" in str(link) or "company-article" in str(link):
            parts = [p for p in str(link).split("/") if p]
            for i, part in enumerate(parts):
                if part.lower() in ("stockpricequote", "company-article", "news") and i + 1 < len(parts):
                    candidate = parts[i + 1].lower()
                    if candidate.isalpha() and len(candidate) > 3:
                        return candidate
    return None


def _parse_mc_date(text: str) -> datetime | None:
    text = text.strip()
    if not text:
        return None
    for pat in _DATE_PATTERNS:
        m = pat.search(text)
        if m:
            try:
                if pat.pattern.startswith(r"\b(\d"):
                    d, mo, y = m.groups()
                    dt = datetime(int(y), int(mo), int(d), tzinfo=IST)
                else:
                    mo_s, d, y = m.groups()
                    dt = date_parser.parse(f"{d} {mo_s} {y}")
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=IST)
                return dt.astimezone(timezone.utc)
            except (ValueError, TypeError):
                pass
    try:
        dt = date_parser.parse(text, fuzzy=True, dayfirst=True)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=IST)
        return dt.astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None


def _http_get(url: str, *, params: dict | None = None) -> requests.Response | None:
    try:
        if _HAS_CURL_CFFI:
            resp = _cffi_requests.get(
                url,
                params=params,
                headers=_MC_HEADERS,
                timeout=20,
                impersonate="chrome120",
            )
        else:
            resp = requests.get(url, params=params, headers=_MC_HEADERS, timeout=20)
        return resp
    except Exception:
        return None


def _fetch_html(url: str) -> str | None:
    resp = _http_get(url)
    if resp is None or resp.status_code != 200:
        return None
    return resp.text


def _parse_news_html(html: str, symbol: str, limit: int) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    articles: list[dict[str, Any]] = []
    seen: set[str] = set()

    for anchor in soup.find_all("a", href=True):
        href = anchor.get("href", "")
        title = anchor.get_text(" ", strip=True)
        if not title or len(title) < 12:
            continue
        if "/news/" not in href and "/company-article/" not in href:
            continue
        if not href.startswith("http"):
            href = "https://www.moneycontrol.com" + href
        if href in seen:
            continue
        if symbol.upper() not in title.upper() and len(articles) > 5:
            parent_text = ""
            parent = anchor.parent
            for _ in range(4):
                if parent:
                    parent_text += " " + parent.get_text(" ", strip=True)
                    parent = parent.parent
            if symbol.upper() not in parent_text.upper()[:200]:
                continue

        pub_dt = None
        node = anchor
        for _ in range(5):
            if node is None:
                break
            blob = node.get_text(" ", strip=True)
            pub_dt = _parse_mc_date(blob)
            if pub_dt:
                break
            node = node.parent

        seen.add(href)
        articles.append(
            {
                "title": title[:300],
                "url": href,
                "source": "moneycontrol",
                "publisher": "Moneycontrol",
                "published_at": pub_dt.isoformat() if pub_dt else None,
                "summary": None,
            }
        )
        if len(articles) >= limit:
            break

    return articles


def fetch_moneycontrol_news(nse_symbol: str, limit: int = 50) -> list[dict[str, Any]]:
    sym = nse_symbol.upper().strip().replace(".NS", "")
    slug = resolve_moneycontrol_slug(sym)
    if not slug:
        return []

    urls = [
        f"https://www.moneycontrol.com/company-article/{slug}/news/{sym}",
        f"https://www.moneycontrol.com/news/{slug}/news/{sym}",
        f"https://www.moneycontrol.com/india/stockpricequote/{slug}/{sym}",
    ]

    for url in urls:
        html = _fetch_html(url)
        if not html:
            continue
        articles = _parse_news_html(html, sym, limit)
        if articles:
            return articles
    return []
