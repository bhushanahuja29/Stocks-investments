from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable

import requests

from ..backend_client import BackendClient
from ..models import JarvisResponse
from ..data.index_constituents import normalize_index_id
from ..news_format import format_news_speech
from .local_market import compute_index_movers_local, compute_nifty_movers_local, list_nifty50_local
from .local_news import get_scrip_news_local


TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "list_nifty50",
        "description": "List all Nifty 50 stock symbols and company names.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_index_movers",
        "description": (
            "Indian index stocks filtered by % move. index: nifty50, banknifty, or finnifty. "
            "Use banknifty for bank/banking stocks. direction: up, down, or any. sort: desc or asc."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "index": {
                    "type": "string",
                    "enum": ["nifty50", "banknifty", "finnifty"],
                    "description": "Index to scan",
                },
                "min_pct": {"type": "number", "description": "Minimum % move threshold"},
                "period": {
                    "type": "string",
                    "enum": ["daily", "weekly", "monthly"],
                    "description": "vs previous day, week, or month close",
                },
                "direction": {
                    "type": "string",
                    "enum": ["up", "down", "any"],
                    "description": "up=gainers only, down=losers only, any=both",
                },
                "sort": {
                    "type": "string",
                    "enum": ["desc", "asc"],
                    "description": "Sort by signed % change",
                },
            },
            "required": ["index", "min_pct"],
        },
    },
    {
        "name": "get_nifty_movers",
        "description": "Deprecated: use get_index_movers with index=nifty50. Nifty 50 movers only.",
        "parameters": {
            "type": "object",
            "properties": {
                "min_pct": {"type": "number"},
                "period": {"type": "string", "enum": ["daily", "weekly", "monthly"]},
            },
            "required": ["min_pct"],
        },
    },
    {
        "name": "get_watchlist_crypto_movers",
        "description": "Get crypto symbols from Mongo watchlist that moved at least min_pct percent today.",
        "parameters": {
            "type": "object",
            "properties": {"min_pct": {"type": "number", "description": "Minimum absolute daily % move"}},
            "required": ["min_pct"],
        },
    },
    {
        "name": "get_monitored_scrips",
        "description": "List all active monitored scrips from Mongo with trigger level counts.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "analyze_symbol",
        "description": "Analyze one symbol: price vs nearest trigger level from Mongo.",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "market_type": {"type": "string", "enum": ["crypto", "indian_stock", "forex"]},
            },
            "required": ["symbol"],
        },
    },
    {
        "name": "get_stock_news",
        "description": (
            "Headlines for a stock from Yahoo Finance and Moneycontrol. "
            "Pass year and month when user asks for a specific month (e.g. June 2026)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "NSE symbol or crypto ticker"},
                "market_type": {
                    "type": "string",
                    "enum": ["crypto", "indian_stocks", "indian_stock"],
                },
                "year": {"type": "integer", "description": "Calendar year e.g. 2026"},
                "month": {"type": "integer", "description": "Month 1-12"},
                "limit": {"type": "integer", "description": "Max articles to return"},
            },
            "required": ["symbol"],
        },
    },
    {
        "name": "analyze_all_near_trigger",
        "description": "List watchlist symbols within threshold_pct of their trigger levels.",
        "parameters": {
            "type": "object",
            "properties": {
                "threshold_pct": {"type": "number", "description": "Distance threshold in percent"},
            },
            "required": ["threshold_pct"],
        },
    },
]


def _is_market_api_missing(exc: Exception) -> bool:
    if isinstance(exc, requests.HTTPError) and exc.response is not None:
        return exc.response.status_code == 404
    text = str(exc).lower()
    return "404" in text and "market" in text


@dataclass
class MarketTools:
    backend: BackendClient
    intent_analyze_symbol: Callable[[str, str], JarvisResponse]
    intent_analyze_all: Callable[[float], JarvisResponse]
    on_progress: Callable[[str], None] | None = None

    def _notify(self, message: str) -> None:
        if self.on_progress:
            self.on_progress(message)

    def _fetch_index_movers(
        self,
        index: str,
        min_pct: float,
        period: str,
        direction: str,
        sort: str,
    ) -> dict[str, Any]:
        index = normalize_index_id(index)
        period = period if period in ("daily", "weekly", "monthly") else "daily"
        direction = direction if direction in ("up", "down", "any") else "any"
        sort = sort if sort in ("desc", "asc") else "desc"
        self._notify(
            f"Scanning {index} {period} movers ({direction}, ≥{min_pct}%) — NSE-aligned Yahoo…"
        )
        try:
            return self.backend.get_index_movers(
                index, min_pct, period=period, direction=direction, sort=sort
            )
        except Exception as exc:
            if _is_market_api_missing(exc):
                self._notify("Backend market API missing — using local Yahoo quotes")
                return compute_index_movers_local(
                    index, min_pct, period=period, direction=direction, sort=sort
                )
            raise

    def execute(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        try:
            if name == "get_index_movers":
                return self._fetch_index_movers(
                    str(args.get("index", "nifty50")),
                    float(args.get("min_pct", 2.0)),
                    str(args.get("period", "daily")).lower(),
                    str(args.get("direction", "any")).lower(),
                    str(args.get("sort", "desc")).lower(),
                )
            if name == "list_nifty50":
                self._notify("Fetching Nifty 50 list…")
                try:
                    data = self.backend.get_nifty50()
                except Exception as exc:
                    if _is_market_api_missing(exc):
                        self._notify("Backend market API missing — using local Nifty 50 list")
                        data = list_nifty50_local()
                    else:
                        raise
                return data if isinstance(data, dict) and data.get("success") else {"success": True, "data": data}
            if name == "get_nifty_movers":
                min_pct = float(args.get("min_pct", 2.0))
                period = str(args.get("period", "daily")).lower()
                return self._fetch_index_movers("nifty50", min_pct, period, "any", "desc")
            if name == "get_watchlist_crypto_movers":
                min_pct = float(args.get("min_pct", 2.0))
                self._notify(f"Scanning watchlist crypto movers (≥{min_pct}%)…")
                data = self.backend.get_watchlist_movers(min_pct, market_type="crypto")
                return {"success": True, "data": data}
            if name == "get_monitored_scrips":
                self._notify("Loading monitored scrips from Mongo…")
                scrips = self.backend.get_scrips()
                summary = [
                    {
                        "symbol": s.get("symbol"),
                        "market_type": s.get("market_type"),
                        "levels": len(s.get("trigger_levels") or []),
                    }
                    for s in scrips
                ]
                return {"success": True, "data": {"scrips": summary, "count": len(summary)}}
            if name == "get_stock_news":
                symbol = str(args.get("symbol", ""))
                market = str(args.get("market_type", "indian_stocks"))
                year = args.get("year")
                month = args.get("month")
                limit = int(args.get("limit", 30))
                self._notify(f"Fetching news for {symbol}…")
                try:
                    payload = self.backend.get_scrip_news(
                        symbol,
                        market_type=market,
                        year=int(year) if year is not None else None,
                        month=int(month) if month is not None else None,
                        limit=limit,
                    )
                except Exception as exc:
                    if _is_market_api_missing(exc):
                        self._notify("Backend news API missing — using local fetch")
                        payload = get_scrip_news_local(
                            symbol,
                            market_type=market,
                            year=int(year) if year is not None else None,
                            month=int(month) if month is not None else None,
                            limit=limit,
                        )
                    else:
                        raise
                return {"success": True, "data": payload, "spoken": format_news_speech(payload)}
            if name == "analyze_symbol":
                symbol = str(args.get("symbol", ""))
                market = str(args.get("market_type", "crypto"))
                result = self.intent_analyze_symbol(symbol, market)
                return {"success": True, "answer": result.text}
            if name == "analyze_all_near_trigger":
                threshold = float(args.get("threshold_pct", 2.0))
                result = self.intent_analyze_all(threshold)
                return {"success": True, "answer": result.text}
            return {"success": False, "error": f"Unknown tool: {name}"}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    @staticmethod
    def tools_prompt() -> str:
        return json.dumps(TOOL_DEFINITIONS, indent=2)
