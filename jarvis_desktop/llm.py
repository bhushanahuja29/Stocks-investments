from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

import requests


@dataclass
class OllamaClient:
    base_url: str = "http://127.0.0.1:11434"
    model: str = "llama3.1:8b"
    timeout_seconds: int = 90

    def answer(self, prompt: str) -> str:
        """Legacy single-prompt generate (symbol hints, short fallback)."""
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={"model": self.model, "prompt": prompt, "stream": False},
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        return str(data.get("response", "")).strip() or "I could not generate a response."

    def chat(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Call Ollama /api/chat; returns full message dict (content + optional tool_calls)."""
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }
        if tools:
            payload["tools"] = tools
        response = requests.post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("message") or {}

    def resolve_symbol(self, user_text: str, known_symbols: list[str]) -> str:
        known_sample = ", ".join(known_symbols[:40])
        prompt = (
            "Map the user message to exactly one trading symbol.\n"
            f"Known symbols: {known_sample}\n"
            "Examples: btc/bitcoin/btcusdt -> BTCUSDT; eth/ethereum -> ETHUSDT.\n"
            "Reply with ONLY the symbol ticker.\n"
            f"User: {user_text}\n"
            "Symbol:"
        )
        raw = self.answer(prompt).strip().upper()
        token = raw.split()[0] if raw.split() else ""
        return "".join(ch for ch in token if ch.isalnum() or ch in ".-/")


_REACT_JSON = re.compile(
    r'\{[\s\S]*?"tool"\s*:\s*"([^"]+)"[\s\S]*?"args"\s*:\s*(\{[\s\S]*?\})[\s\S]*?\}',
    re.IGNORECASE,
)


def _parse_tool_object(obj: dict[str, Any]) -> tuple[str, dict[str, Any]] | None:
    if "tool" in obj:
        name = str(obj["tool"])
        args = obj.get("args") or {}
        return name, args if isinstance(args, dict) else {}
    if "name" in obj:
        name = str(obj["name"])
        params = obj.get("parameters") or obj.get("args") or {}
        return name, params if isinstance(params, dict) else {}
    return None


def _iter_json_objects(text: str):
    start = 0
    while True:
        i = text.find("{", start)
        if i < 0:
            break
        depth = 0
        for j in range(i, len(text)):
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
                if depth == 0:
                    yield text[i : j + 1]
                    start = j + 1
                    break
        else:
            break


def parse_react_tool_call(text: str) -> tuple[str, dict[str, Any]] | None:
    """Parse tool calls from model text (ReAct or Ollama name/parameters JSON)."""
    text = text.strip()
    if not text:
        return None
    candidates: list[str] = [text]
    block = _extract_json_block(text)
    if block:
        candidates.append(block)
    candidates.extend(_iter_json_objects(text))
    seen: set[str] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        try:
            obj = json.loads(candidate)
            if isinstance(obj, dict):
                parsed = _parse_tool_object(obj)
                if parsed:
                    return parsed
        except json.JSONDecodeError:
            pass
    match = _REACT_JSON.search(text)
    if match:
        try:
            args = json.loads(match.group(2))
            return match.group(1), args if isinstance(args, dict) else {}
        except json.JSONDecodeError:
            pass
    return None


def _extract_json_block(text: str) -> str | None:
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return text[start : end + 1]
    return None


def message_content(message: dict[str, Any]) -> str:
    return str(message.get("content", "")).strip()


def message_tool_calls(message: dict[str, Any]) -> list[dict[str, Any]]:
    """Native Ollama tool_calls if present."""
    calls = message.get("tool_calls")
    if not isinstance(calls, list):
        return []
    return calls
