from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests
from pymongo import MongoClient

from .config import CONFIG


@dataclass
class BackendClient:
    base_url: str = CONFIG.backend_url
    timeout_seconds: int = 30

    def _url(self, path: str) -> str:
        return f"{self.base_url.rstrip('/')}{path}"

    def get_price(self, symbol: str, market_type: str = "crypto") -> float:
        response = requests.get(
            self._url(f"/api/price/{symbol}"),
            params={"market_type": market_type},
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        return float(data["mark_price"])

    def search_zones(
        self,
        symbol: str,
        timeframe: str = "1w",
        market_type: str = "crypto",
        version: str = "v4",
    ) -> dict[str, Any]:
        response = requests.post(
            self._url("/api/zones/search"),
            json={
                "symbol": symbol,
                "timeframe": timeframe,
                "market_type": market_type,
                "version": version,
            },
            timeout=self.timeout_seconds * 2,
        )
        response.raise_for_status()
        return response.json()

    def get_scrips(self) -> list[dict[str, Any]]:
        response = requests.get(self._url("/api/scrips"), timeout=self.timeout_seconds)
        response.raise_for_status()
        data = response.json()
        return data.get("scrips", [])

    def find_scrip(self, symbol: str) -> dict[str, Any] | None:
        """Load monitored scrip from backend (backend reads MongoDB)."""
        target = symbol.upper().strip()
        for scrip in self.get_scrips():
            if str(scrip.get("symbol", "")).upper() == target:
                return scrip
        return None

    def health(self) -> dict[str, Any]:
        response = requests.get(self._url("/api/health"), timeout=self.timeout_seconds)
        response.raise_for_status()
        return response.json()

    def get_nifty50(self) -> dict[str, Any]:
        response = requests.get(self._url("/api/market/nifty50"), timeout=self.timeout_seconds)
        response.raise_for_status()
        return response.json()

    def get_index_movers(
        self,
        index: str,
        min_pct: float,
        period: str = "daily",
        direction: str = "any",
        sort: str = "desc",
    ) -> dict[str, Any]:
        response = requests.get(
            self._url("/api/market/index-movers"),
            params={
                "index": index,
                "min_pct": min_pct,
                "period": period,
                "direction": direction,
                "sort": sort,
            },
            timeout=self.timeout_seconds * 8,
        )
        response.raise_for_status()
        return response.json()

    def get_nifty_movers(self, min_pct: float, period: str = "daily") -> dict[str, Any]:
        return self.get_index_movers("nifty50", min_pct, period=period, direction="any", sort="desc")

    def get_scrip_news(
        self,
        symbol: str,
        market_type: str = "indian_stocks",
        year: int | None = None,
        month: int | None = None,
        limit: int = 30,
        sources: str = "yahoo,moneycontrol",
    ) -> dict[str, Any]:
        mtype = market_type
        if mtype in ("indian_stock", "indian_stocks"):
            mtype = "indian_stocks"
        params: dict[str, Any] = {
            "market_type": mtype,
            "limit": limit,
            "sources": sources,
        }
        if year is not None:
            params["year"] = year
        if month is not None:
            params["month"] = month
        response = requests.get(
            self._url(f"/api/market/news/{symbol}"),
            params=params,
            timeout=60,
        )
        response.raise_for_status()
        return response.json()

    def get_market_quote(self, symbol: str, market_type: str = "crypto") -> dict[str, Any]:
        mtype = market_type
        if mtype in ("indian_stock", "indian_stocks"):
            mtype = "indian_stocks"
        response = requests.get(
            self._url(f"/api/market/quote/{symbol}"),
            params={"market_type": mtype},
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        return response.json()

    def get_market_dashboard(self) -> dict[str, Any]:
        response = requests.get(
            self._url("/api/market/dashboard"),
            timeout=self.timeout_seconds * 2,
        )
        response.raise_for_status()
        return response.json()

    def sync_pins(self, entries: list[dict[str, Any]]) -> dict[str, Any]:
        """Push global pin list to Crypto Levels MongoDB for mobile alerts."""
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if CONFIG.jarvis_sync_key:
            headers["X-Jarvis-Key"] = CONFIG.jarvis_sync_key
        payload = {
            "pins": [
                {
                    "symbol": e.get("symbol"),
                    "market_type": e.get("market_type", "crypto"),
                    "alert_above": e.get("alert_above"),
                    "alert_below": e.get("alert_below"),
                }
                for e in entries
            ]
        }
        response = requests.post(
            self._url("/api/pins/sync"),
            json=payload,
            headers=headers,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        return response.json()

    def stop_pin_alert(self, symbol: str) -> dict[str, Any]:
        """Silence repeating pin alerts on the server."""
        headers: dict[str, str] = {}
        if CONFIG.jarvis_sync_key:
            headers["X-Jarvis-Key"] = CONFIG.jarvis_sync_key
        response = requests.post(
            self._url(f"/api/pins/{symbol.upper().strip()}/stop-alert"),
            headers=headers,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        return response.json()

    def get_watchlist_movers(self, min_pct: float, market_type: str | None = None) -> dict[str, Any]:
        params: dict[str, Any] = {"min_pct": min_pct}
        if market_type:
            params["market_type"] = market_type
        response = requests.get(
            self._url("/api/market/watchlist-movers"),
            params=params,
            timeout=self.timeout_seconds * 4,
        )
        response.raise_for_status()
        return response.json()


@dataclass
class MongoLevelClient:
    mongo_uri: str = CONFIG.mongo_uri
    db_name: str = CONFIG.mongo_db
    collection_name: str = CONFIG.mongo_collection

    def __post_init__(self) -> None:
        self._client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=5000)
        self._collection = self._client[self.db_name][self.collection_name]

    def get_symbol(self, symbol: str) -> dict[str, Any] | None:
        return self._collection.find_one({"symbol": symbol.upper(), "active": True})

    def get_all_active(self) -> list[dict[str, Any]]:
        return list(self._collection.find({"active": True, "monitoring_type": "multi_level"}))
