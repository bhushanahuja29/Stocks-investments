from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from typing import Any, Callable

import requests

from .config import CONFIG
from .llm import OllamaClient, message_content, message_tool_calls, parse_react_tool_call
from .models import JarvisResponse
from .movers_format import format_movers_speech, movers_table_payload
from .news_format import format_news_log, format_news_speech
from .tools.market_data import TOOL_DEFINITIONS, MarketTools


_AGENT_KEYWORDS = (
    "nifty",
    "nifty50",
    "nifty 50",
    "bank nifty",
    "banknifty",
    "fin nifty",
    "finnifty",
    "banking",
    "bank stock",
    "moved",
    "move ",
    "percent",
    "%",
    "today",
    "movers",
    "gainers",
    "losers",
    "watchlist",
    "which crypto",
    "which stock",
    "show all",
    "list all",
    "list nifty",
    "get all",
    "get nifty",
    "all stocks",
    "all crypto",
    "how many",
    "market",
    "news",
    "headlines",
    "articles",
)


def is_agent_query(text: str) -> bool:
    """True when message is open-ended market/list/movers query (not single-symbol analyze)."""
    lower = text.lower().strip()
    if not lower:
        return False
    # Fast-path analyze phrases should not go to agent
    if any(k in lower for k in ("analyze btc", "analyse btc", "analyze bitcoin")):
        return False
    if "analyze all" in lower or "analyse all" in lower:
        return False
    if "near trigger" in lower or "morning" in lower:
        return False
    if any(kw in lower for kw in _AGENT_KEYWORDS):
        return True
    if re.search(r"\d+\s*%", lower) or "2 percent" in lower:
        if any(w in lower for w in ("moved", "move", "crypto", "stock", "nifty", "watchlist", "today")):
            return True
    return False


def _ollama_tools_schema() -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["parameters"],
            },
        }
        for t in TOOL_DEFINITIONS
    ]


def _clean_movers(movers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    clean: list[dict[str, Any]] = []
    for row in movers:
        pct = row.get("change_pct")
        price = row.get("price")
        try:
            pct_f = float(pct)
            if not math.isfinite(pct_f):
                continue
        except (TypeError, ValueError):
            continue
        try:
            price_f = float(price)
            if not math.isfinite(price_f) or price_f <= 0:
                continue
        except (TypeError, ValueError):
            continue
        clean.append(
            {
                **row,
                "price": round(price_f, 2),
                "change_pct": round(pct_f, 2),
            }
        )
    return clean


def _summarize_tool_result(name: str, result: dict[str, Any], max_items: int = 15) -> str:
    """Compact JSON for model context; cap long mover lists for token budget."""
    if not result.get("success"):
        return json.dumps(result)
    data = result.get("data") or result
    if name in ("get_index_movers", "get_nifty_movers", "get_watchlist_crypto_movers"):
        if isinstance(data, dict) and "data" in data and isinstance(data["data"], dict):
            data = data["data"]
        movers = data.get("movers") if isinstance(data, dict) else None
        if isinstance(movers, list):
            movers = _clean_movers(movers)
            data = {**data, "movers": movers, "count": len(movers)}
        if isinstance(movers, list) and len(movers) > max_items:
            trimmed = movers[:max_items]
            out = {**data, "movers": trimmed, "truncated": True, "total_count": len(movers)}
            return json.dumps(out)
    if name == "list_nifty50":
        stocks = data.get("stocks") if isinstance(data, dict) else None
        if isinstance(stocks, list) and len(stocks) > max_items:
            out = {**data, "stocks": stocks[:max_items], "truncated": True, "total_count": len(stocks)}
            return json.dumps(out)
    return json.dumps(result)


def _spoken_summary(full_text: str, max_chars: int = 600) -> str:
    if len(full_text) <= max_chars:
        return full_text
    return full_text[: max_chars - 40].rsplit(" ", 1)[0] + f"... ({len(full_text)} chars in log)"


def _movers_payload(result: dict[str, Any]) -> dict[str, Any] | None:
    if not result.get("success"):
        return None
    data = result.get("data") or result
    if isinstance(data, dict) and "data" in data and isinstance(data["data"], dict):
        data = data["data"]
    if isinstance(data, dict) and isinstance(data.get("movers"), list):
        return data
    return None


@dataclass
class KryptoAgent:
    llm: OllamaClient
    tools: MarketTools
    max_steps: int = field(default_factory=lambda: CONFIG.agent_max_steps)
    on_step: Callable[[str], None] | None = None
    on_llm: Callable[[str], None] | None = None
    on_tool: Callable[[str], None] | None = None

    def _progress(self, message: str) -> None:
        if self.on_step:
            self.on_step(message)
        elif self.on_llm:
            self.on_llm(message)

    def _movers_response_if_ready(
        self,
        tool_name: str,
        result: dict[str, Any],
        log_parts: list[str],
    ) -> JarvisResponse | None:
        if tool_name in ("get_index_movers", "get_nifty_movers"):
            payload = _movers_payload(result)
            if payload is None:
                return None
            spoken = format_movers_speech(payload)
            return JarvisResponse(
                spoken,
                payload=movers_table_payload(payload),
            )
        if tool_name == "get_watchlist_crypto_movers":
            payload = _movers_payload(result)
            if payload is None:
                return None
            spoken = format_movers_speech(payload, label="watchlist crypto")
            return JarvisResponse(
                spoken,
                payload=movers_table_payload(payload, label="watchlist crypto"),
            )
        return None

    def _news_response_if_ready(
        self,
        tool_name: str,
        result: dict[str, Any],
        log_parts: list[str],
    ) -> JarvisResponse | None:
        if tool_name != "get_stock_news" or not result.get("success"):
            return None
        payload = result.get("data")
        if not isinstance(payload, dict):
            return None
        spoken = result.get("spoken") or format_news_speech(payload)
        detail = format_news_log(payload) + "\n---\nTool trace:\n" + "\n".join(log_parts)
        return JarvisResponse(spoken, log_detail=detail)

    def run(self, user_message: str) -> JarvisResponse:
        system = (
            "You are Krypto, Bhushan's trading assistant for crypto and Indian markets. "
            "Always use tools for live prices, Nifty lists, and watchlist movers—never guess numbers. "
            "Only report prices and % changes that appear in tool JSON; never invent values. "
            "For Indian index scans use get_index_movers with index=nifty50|banknifty|finnifty. "
            "Bank questions MUST use index=banknifty. Fin questions use index=finnifty. "
            "Pass direction (up/down/any) and sort (desc/asc) when user asks. "
            "For stock news use get_stock_news with symbol, market_type, year, month when user names a month. "
            "When you need data, respond with ONLY a JSON object: "
            '{"tool": "tool_name", "args": {...}}. '
            "After receiving tool results, answer in clear natural language. "
            "Summarize mover lists: mention count and top movers by magnitude. "
            f"Available tools:\n{MarketTools.tools_prompt()}"
        )
        messages: list[dict[str, str]] = [
            {"role": "system", "content": system},
            {"role": "user", "content": user_message},
        ]
        ollama_tools = _ollama_tools_schema()
        full_log_parts: list[str] = []

        for step in range(self.max_steps):
            self._progress(f"Ollama thinking (step {step + 1}/{self.max_steps})…")

            try:
                message = self.llm.chat(messages, tools=ollama_tools)
            except requests.RequestException as exc:
                return JarvisResponse(f"Ollama is unavailable: {exc}")

            content = message_content(message)
            tool_calls = message_tool_calls(message)

            # Native tool calls
            if tool_calls:
                messages.append({"role": "assistant", "content": content or "", "tool_calls": tool_calls})
                for call in tool_calls:
                    fn = call.get("function") or {}
                    name = str(fn.get("name", ""))
                    raw_args = fn.get("arguments", "{}")
                    try:
                        args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                    except json.JSONDecodeError:
                        args = {}
                    if not isinstance(args, dict):
                        args = {}
                    if self.on_tool:
                        self.on_tool(f"Running tool: {name}")
                    result = self.tools.execute(name, args)
                    summary = _summarize_tool_result(name, result)
                    full_log_parts.append(f"[tool {name}] {summary[:8000]}")
                    early = self._movers_response_if_ready(name, result, full_log_parts)
                    if early:
                        return early
                    early = self._news_response_if_ready(name, result, full_log_parts)
                    if early:
                        return early
                    messages.append({"role": "tool", "content": summary})
                continue

            # JSON tool call embedded in text (ReAct or {"name":..., "parameters":...})
            parsed = parse_react_tool_call(content)
            if parsed:
                name, args = parsed
                if self.on_tool:
                    self.on_tool(f"Running tool: {name}")
                result = self.tools.execute(name, args)
                summary = _summarize_tool_result(name, result)
                full_log_parts.append(f"[tool {name}] {summary[:8000]}")
                early = self._movers_response_if_ready(name, result, full_log_parts)
                if early:
                    return early
                early = self._news_response_if_ready(name, result, full_log_parts)
                if early:
                    return early
                messages.append({"role": "assistant", "content": content})
                messages.append(
                    {
                        "role": "user",
                        "content": f"Tool {name} result:\n{summary}\n\nNow answer Bhushan concisely.",
                    }
                )
                continue

            # Final natural answer (no executable tool JSON in response)
            if content and not parse_react_tool_call(content):
                spoken = _spoken_summary(content)
                if full_log_parts:
                    detail = content + "\n\n---\nTool trace:\n" + "\n".join(full_log_parts)
                    return JarvisResponse(spoken, log_detail=detail)
                return JarvisResponse(spoken)
            break

        return JarvisResponse(
            "I ran several tool steps but could not finish. Please try a simpler question."
        )
