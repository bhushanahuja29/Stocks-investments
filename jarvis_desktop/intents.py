from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Callable

import requests

from .automation import MissingLevelAutomation
from .backend_client import BackendClient, MongoLevelClient
from .config import CONFIG
from .agent import KryptoAgent, format_movers_speech, is_agent_query
from .news_format import format_news_log, format_news_speech
from .news_query_parser import parse_news_query
from .pin_commands import format_pin_confirmation, parse_pin_command
from .pin_panel import _MAX_PINS
from .market_updates import format_market_updates_speech, is_market_updates_query
from .query_parser import parse_mover_query
from .tools.local_dashboard import get_market_dashboard_local
from .tools.local_news import get_scrip_news_local
from .llm import OllamaClient
from .models import JarvisResponse
from .symbol_resolver import SymbolResolver, canonical_crypto_symbol
from .tools.market_data import MarketTools


def _distance_pct(current: float, trigger: float) -> float:
    if trigger == 0:
        return 0.0
    return ((current - trigger) / trigger) * 100.0


@dataclass
class IntentRouter:
    backend: BackendClient
    mongo: MongoLevelClient
    automation: MissingLevelAutomation
    llm: OllamaClient | None = None
    on_agent_progress: Callable[[str], None] | None = None
    pin_panel: Any = None

    def __post_init__(self) -> None:
        self.resolver = SymbolResolver(mongo=self.mongo, llm=self.llm)
        self._agent: KryptoAgent | None = None

    def _get_agent(self) -> KryptoAgent | None:
        if not self.llm:
            return None
        if self._agent is None:
            progress = self.on_agent_progress
            tools = MarketTools(
                backend=self.backend,
                intent_analyze_symbol=lambda s, m: self.analyze_symbol(s, m),
                intent_analyze_all=lambda t: self.analyze_all_symbols(t),
                on_progress=progress,
            )
            self._agent = KryptoAgent(
                llm=self.llm,
                tools=tools,
                on_step=progress,
                on_tool=progress,
            )
        return self._agent

    def handle(self, spoken_text: str) -> JarvisResponse:
        text = spoken_text.lower().strip()
        if not text:
            return JarvisResponse("I did not catch that. Please repeat.")
        if self._is_analyze_all_command(text):
            threshold = self._extract_threshold_pct(text) or CONFIG.near_trigger_threshold
            return self.analyze_all_symbols(threshold)

        if "near trigger" in text or ("morning" in text and "market update" not in text):
            return self.analyze_all_symbols(CONFIG.near_trigger_threshold)

        if is_market_updates_query(spoken_text):
            try:
                payload = self.backend.get_market_dashboard()
            except requests.RequestException:
                try:
                    payload = get_market_dashboard_local()
                except Exception as exc:
                    return JarvisResponse(f"Could not fetch market updates: {exc}")
            spoken = format_market_updates_speech(payload)
            try:
                detail = json.dumps(payload, indent=2, default=str)[:6000]
            except TypeError:
                detail = str(payload)[:6000]
            return JarvisResponse(spoken, log_detail=f"---\nMarket dashboard:\n{detail}")

        pin_cmd = parse_pin_command(spoken_text)
        if pin_cmd and self.pin_panel:
            if pin_cmd.action == "unpin_all":
                n = self.pin_panel.unpin()
                if n:
                    return JarvisResponse(f"Removed all {n} pinned scrips from your screen.")
                return JarvisResponse("No pinned scrips on screen.")
            if pin_cmd.action == "unpin":
                if pin_cmd.symbol_text:
                    resolved = self.resolver._resolve_from_speech_inner(pin_cmd.symbol_text)
                    if not resolved:
                        token = pin_cmd.symbol_text.strip().split()[-1]
                        resolved = self.resolver.resolve(token, spoken_context=spoken_text)
                    if resolved and self.pin_panel.unpin(resolved.symbol):
                        return JarvisResponse(f"Unpinned {resolved.symbol}.")
                    return JarvisResponse(
                        f"{pin_cmd.symbol_text} is not pinned. Say unpin all to clear every pin."
                    )
                n = self.pin_panel.unpin()
                if n == 1:
                    return JarvisResponse("Removed the pinned scrip from your screen.")
                if n > 1:
                    return JarvisResponse(f"Removed all {n} pinned scrips from your screen.")
                return JarvisResponse("No pinned scrips on screen.")
            if pin_cmd.action == "pin":
                resolved = self.resolver._resolve_from_speech_inner(spoken_text)
                if not resolved and pin_cmd.symbol_text:
                    resolved = self.resolver._resolve_from_speech_inner(pin_cmd.symbol_text)
                if not resolved and pin_cmd.symbol_text:
                    token = pin_cmd.symbol_text.strip().split()[-1]
                    resolved = self.resolver.resolve(token, spoken_context=spoken_text)
                if not resolved:
                    return JarvisResponse(
                        "I could not tell which symbol to pin. Try pin reliance or pin btc."
                    )
                already = self.pin_panel.is_pinned(resolved.symbol)
                quote = self.pin_panel.pin(resolved.symbol, resolved.market_type)
                if quote is None and not already:
                    return JarvisResponse(
                        f"Maximum {_MAX_PINS} pinned scrips. Unpin one first or say unpin all."
                    )
                if quote:
                    prefix = "Updated" if already else "Pinned"
                    return JarvisResponse(
                        format_pin_confirmation(quote).replace("Pinned", prefix, 1)
                    )
                suffix = " Refreshed." if already else ""
                return JarvisResponse(
                    f"Pinned {resolved.symbol}. Hover its tab on the right for live price.{suffix}"
                )

        news_query = parse_news_query(spoken_text)
        if news_query:
            resolved = self.resolver._resolve_from_speech_inner(news_query.symbol_text)
            if not resolved:
                resolved = self.resolver._resolve_from_speech_inner(spoken_text)
            if not resolved:
                token = news_query.symbol_text.strip().split()[-1]
                resolved = self.resolver.resolve(token, spoken_context=spoken_text)
            if not resolved:
                return JarvisResponse(
                    "I could not tell which symbol. Try get news of TCS June 2026."
                )
            mtype = resolved.market_type
            if mtype in ("indian_stock",):
                mtype = "indian_stocks"
            try:
                payload = self.backend.get_scrip_news(
                    resolved.symbol,
                    market_type=mtype,
                    year=news_query.year,
                    month=news_query.month,
                    limit=news_query.limit,
                )
            except requests.RequestException:
                try:
                    payload = get_scrip_news_local(
                        resolved.symbol,
                        market_type=mtype,
                        year=news_query.year,
                        month=news_query.month,
                        limit=news_query.limit,
                    )
                except Exception as exc:
                    return JarvisResponse(f"Could not fetch news: {exc}")
            spoken = format_news_speech(payload)
            return JarvisResponse(
                spoken,
                log_detail=format_news_log(payload),
            )

        mover_query = parse_mover_query(spoken_text)
        if mover_query:
            tools = MarketTools(
                backend=self.backend,
                intent_analyze_symbol=lambda s, m: self.analyze_symbol(s, m),
                intent_analyze_all=lambda t: self.analyze_all_symbols(t),
                on_progress=self.on_agent_progress,
            )
            try:
                result = tools.execute("get_index_movers", mover_query.to_tool_args())
                if result.get("success"):
                    spoken = format_movers_speech(result)
                    try:
                        trace = json.dumps(result, indent=2, default=str)[:8000]
                    except TypeError:
                        trace = str(result)[:8000]
                    return JarvisResponse(
                        spoken,
                        log_detail=f"---\nTool trace:\n[tool get_index_movers] {trace}",
                    )
            except requests.RequestException:
                pass

        # Agent before single-symbol analyze — "list nifty stocks" must not resolve LIST as a ticker
        if is_agent_query(text):
            agent = self._get_agent()
            if agent:
                try:
                    return agent.run(spoken_text)
                except requests.RequestException:
                    pass

        if self._is_single_symbol_analysis(text):
            resolved = self.resolver.resolve_from_speech(spoken_text)
            if resolved:
                label = resolved.symbol
                if resolved.matched_via in ("watchlist", "mongo", "llm+mongo"):
                    label = f"{resolved.symbol} (matched from your request)"
                result = self.analyze_resolved(resolved)
                if resolved.matched_via.startswith("llm") or resolved.symbol != spoken_text.upper():
                    return JarvisResponse(f"Understood as {label}. {result.text}")
                return result

        if self.llm:
            try:
                prompt = (
                    "You are Krypto assistant for Bhushan. Keep replies under 2 short sentences. "
                    f"User said: {spoken_text}"
                )
                return JarvisResponse(self.llm.answer(prompt))
            except requests.RequestException:
                pass
        return JarvisResponse("Please tell me a symbol, for example analyze BTC.")

    def analyze_symbol(self, symbol: str, market_type: str) -> JarvisResponse:
        resolved = self.resolver.resolve(symbol, spoken_context=symbol)
        if not resolved:
            return JarvisResponse(f"I could not resolve symbol {symbol}.")
        return self.analyze_resolved(resolved)

    def analyze_resolved(self, resolved) -> JarvisResponse:
        normalized = canonical_crypto_symbol(resolved.symbol)
        doc = resolved.doc
        market_type = resolved.market_type

        if doc is None:
            doc = self._load_scrip_doc(normalized)

        if doc is None:
            if market_type in ("crypto", "forex"):
                return self._analyze_via_backend(normalized, market_type)
            ok, err = self.automation.build_levels_for_symbol(normalized)
            if not ok:
                fallback = self._analyze_via_backend(normalized, "indian_stock")
                if "could not" not in fallback.text.lower() and "search failed" not in fallback.text.lower():
                    return JarvisResponse(
                        f"Screenshot pipeline unavailable ({err}). Using live zone search. {fallback.text}"
                    )
                return JarvisResponse(f"Could not build levels for {normalized}. Pipeline error: {err}")
            doc = self.mongo.get_symbol(normalized)
            if doc is None:
                return self._analyze_via_backend(normalized, "indian_stock")

        market = doc.get("market_type", market_type)
        trading_symbol = canonical_crypto_symbol(str(doc.get("symbol", normalized)))
        try:
            price = self.backend.get_price(trading_symbol, market_type=market)
        except requests.RequestException as exc:
            return JarvisResponse(f"I could not fetch live price for {trading_symbol}: {exc}")

        levels = doc.get("trigger_levels") or []
        if not isinstance(levels, list) or not levels:
            return self._analyze_via_backend(trading_symbol, market, price=price)

        nearest: dict[str, Any] = min(
            levels, key=lambda lvl: abs(_distance_pct(price, float(lvl.get("trigger_price", 0.0))))
        )
        trigger = float(nearest.get("trigger_price", 0.0))
        dist = _distance_pct(price, trigger)
        tf = nearest.get("timeframe", doc.get("timeframe", "unknown"))
        return JarvisResponse(
            f"{trading_symbol} is at {price:.2f}. Nearest trigger is {trigger:.2f} on {tf}, distance {dist:+.2f} percent."
        )

    def _load_scrip_doc(self, symbol: str) -> dict[str, Any] | None:
        """Prefer backend /api/scrips (Mongo via API), fallback to direct Mongo client."""
        try:
            doc = self.backend.find_scrip(symbol)
            if doc:
                return doc
        except requests.RequestException:
            pass
        return self.mongo.get_symbol(symbol)

    def _analyze_via_backend(
        self,
        symbol: str,
        market_type: str,
        price: float | None = None,
    ) -> JarvisResponse:
        symbol = canonical_crypto_symbol(symbol)
        market_type = "crypto" if symbol.endswith("USDT") else market_type
        try:
            if price is None:
                price = self.backend.get_price(symbol, market_type=market_type)
            search = self.backend.search_zones(symbol, timeframe="1w", market_type=market_type, version="v4")
        except requests.RequestException as exc:
            return JarvisResponse(f"Could not analyze {symbol} from backend: {exc}")

        zones = search.get("zones", [])
        if not zones:
            return JarvisResponse(f"I found no zones for {symbol}.")

        nearest_zone = min(
            zones,
            key=lambda z: abs(_distance_pct(price, float(z.get("top", 0.0)))),
        )
        trigger = float(nearest_zone.get("top", 0.0))
        dist = _distance_pct(price, trigger)
        return JarvisResponse(
            f"{symbol} is at {price:.2f}. Nearest zone trigger is {trigger:.2f}, distance {dist:+.2f} percent."
        )

    def _is_single_symbol_analysis(self, text: str) -> bool:
        """True when user wants one symbol analyzed (not list/nifty/movers queries)."""
        if is_agent_query(text):
            return False
        return any(
            key in text
            for key in (
                "analyze",
                "analyse",
                "check",
                "scrip",
                "level",
                "price",
                "trigger",
                "bitcoin",
                "btc",
            )
        ) or (
            "stock" in text
            and not any(w in text for w in ("nifty", "list", "show", "all", "moved", "movers", "watchlist"))
        )

    def _is_analyze_all_command(self, text: str) -> bool:
        if "analyze all" in text or "analyse all" in text:
            return True
        if "all symbol" in text or "all scrip" in text:
            return True
        if "every symbol" in text or "every scrip" in text:
            return True
        return False

    def _extract_threshold_pct(self, text: str) -> float | None:
        match = re.search(r"(\d+(?:\.\d+)?)\s*%", text)
        if match:
            return float(match.group(1))
        if "2 percent" in text or "2%" in text:
            return 2.0
        return None

    def _load_all_scrips(self) -> list[dict[str, Any]]:
        try:
            scrips = self.backend.get_scrips()
            if scrips:
                return scrips
        except requests.RequestException:
            pass
        return self.mongo.get_all_active()

    def analyze_all_symbols(self, threshold_pct: float) -> JarvisResponse:
        """Scan every monitored symbol from Mongo and list those within threshold of a trigger."""
        hits: list[tuple[float, str]] = []
        scrips = self._load_all_scrips()
        checked = 0

        for scrip in scrips:
            symbol = scrip.get("symbol")
            if not symbol:
                continue
            market = scrip.get("market_type", "crypto")
            trading_symbol = canonical_crypto_symbol(str(symbol))
            levels = scrip.get("trigger_levels") or []
            if not isinstance(levels, list) or not levels:
                continue

            try:
                price = self.backend.get_price(trading_symbol, market_type=market)
            except requests.RequestException:
                continue

            checked += 1
            nearest_dist = float("inf")
            nearest_trigger = 0.0
            nearest_tf = ""
            for level in levels:
                if level.get("alert_disabled"):
                    continue
                trigger = float(level.get("trigger_price", 0.0))
                if trigger <= 0:
                    continue
                dist = abs(_distance_pct(price, trigger))
                if dist < nearest_dist:
                    nearest_dist = dist
                    nearest_trigger = trigger
                    nearest_tf = str(level.get("timeframe", ""))

            if nearest_dist <= threshold_pct:
                tf_note = f" on {nearest_tf}" if nearest_tf else ""
                line = (
                    f"{trading_symbol} at {price:.2f}, "
                    f"{nearest_dist:.2f}% from trigger {nearest_trigger:.2f}{tf_note}"
                )
                hits.append((nearest_dist, line))

        hits.sort(key=lambda item: item[0])
        if not hits:
            return JarvisResponse(
                f"Scanned {checked} symbols from Mongo. "
                f"None are within {threshold_pct:.1f}% of their trigger levels."
            )

        lines = [line for _, line in hits]
        preview = "; ".join(lines[:12])
        extra = ""
        if len(lines) > 12:
            extra = f" And {len(lines) - 12} more."
        return JarvisResponse(
            f"Found {len(lines)} symbols within {threshold_pct:.1f}% of trigger "
            f"(scanned {checked} from Mongo): {preview}.{extra}"
        )

    def near_trigger_report(self, threshold_pct: float) -> JarvisResponse:
        """Alias used by morning scheduler."""
        result = self.analyze_all_symbols(threshold_pct)
        if result.text.startswith("Found "):
            return JarvisResponse("Morning near-trigger report. " + result.text)
        return JarvisResponse("Morning near-trigger report. " + result.text)
