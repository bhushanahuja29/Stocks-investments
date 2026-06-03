from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .llm import OllamaClient

# Common spoken names -> exchange symbols stored in Mongo / Delta API
CRYPTO_ALIASES: dict[str, str] = {
    "BTC": "BTCUSDT",
    "BITCOIN": "BTCUSDT",
    "BTCUSD": "BTCUSDT",
    "ETH": "ETHUSDT",
    "ETHEREUM": "ETHUSDT",
    "ETHUSD": "ETHUSDT",
    "SOL": "SOLUSDT",
    "SOLANA": "SOLUSDT",
    "SOLUSD": "SOLUSDT",
    "XAU": "XAUUSD",
    "GOLD": "XAUUSD",
}


def canonical_crypto_symbol(symbol: str) -> str:
    """Delta Exchange crypto perpetuals use *USDT tickers, not *USD."""
    upper = symbol.upper().strip()
    if upper in CRYPTO_ALIASES:
        return CRYPTO_ALIASES[upper]
    if upper.endswith("USD") and not upper.endswith("USDT"):
        return f"{upper}T"  # BTCUSD -> BTCUSDT
    return upper


@dataclass
class ResolvedSymbol:
    symbol: str
    market_type: str
    doc: dict[str, Any] | None = None
    matched_via: str = "direct"


@dataclass
class SymbolResolver:
    mongo: Any
    llm: OllamaClient | None = None

    def resolve(self, raw: str, spoken_context: str | None = None) -> ResolvedSymbol | None:
        token = self._normalize_token(raw)
        if not token:
            return None

        candidates = self._candidate_symbols(token)
        for candidate in candidates:
            doc = self.mongo.get_symbol(candidate)
            if doc:
                return ResolvedSymbol(
                    symbol=doc["symbol"],
                    market_type=doc.get("market_type", self._guess_market_type(candidate)),
                    doc=doc,
                    matched_via="mongo",
                )

        fuzzy = self._fuzzy_match_in_watchlist(token)
        if fuzzy:
            return fuzzy

        if self.llm and spoken_context:
            llm_symbol = self._resolve_with_llm(spoken_context)
            if llm_symbol:
                for candidate in self._candidate_symbols(llm_symbol):
                    doc = self.mongo.get_symbol(candidate)
                    if doc:
                        return ResolvedSymbol(
                            symbol=doc["symbol"],
                            market_type=doc.get("market_type", self._guess_market_type(candidate)),
                            doc=doc,
                            matched_via="llm+mongo",
                        )
                canonical = self._candidate_symbols(llm_symbol)[0]
                return ResolvedSymbol(
                    symbol=canonical,
                    market_type=self._guess_market_type(canonical),
                    doc=None,
                    matched_via="llm",
                )

        # No Mongo doc — still return best canonical ticker for backend lookup
        canonical = canonical_crypto_symbol(candidates[0] if candidates else token)
        return ResolvedSymbol(
            symbol=canonical,
            market_type=self._guess_market_type(canonical),
            doc=None,
            matched_via="alias",
        )


    def _candidate_symbols(self, token: str) -> list[str]:
        upper = canonical_crypto_symbol(token.upper())
        out: list[str] = []
        if upper in CRYPTO_ALIASES:
            out.append(CRYPTO_ALIASES[upper])
        out.append(upper)
        if upper.endswith("USDT") or upper.endswith("USD"):
            out.append(upper)
        elif len(upper) <= 5 and upper.isalpha():
            out.append(f"{upper}USDT")
        out.append(upper)
        # dedupe preserve order
        seen: set[str] = set()
        ordered: list[str] = []
        for s in out:
            if s not in seen:
                seen.add(s)
                ordered.append(s)
        return ordered

    def _fuzzy_match_in_watchlist(self, token: str) -> ResolvedSymbol | None:
        upper = token.upper()
        aliases = {upper, CRYPTO_ALIASES.get(upper, "")}
        for scrip in self.mongo.get_all_active():
            sym = str(scrip.get("symbol", "")).upper()
            if not sym:
                continue
            base = sym.replace("USDT", "").replace("USD", "").replace(".NS", "")
            if sym == upper or sym.startswith(upper) or base == upper or upper in aliases:
                if upper in ("BTC", "BITCOIN") and "BTC" in sym:
                    return ResolvedSymbol(
                        symbol=sym,
                        market_type=scrip.get("market_type", "crypto"),
                        doc=scrip,
                        matched_via="watchlist",
                    )
                if sym == upper or sym.startswith(upper) or base == upper:
                    return ResolvedSymbol(
                        symbol=sym,
                        market_type=scrip.get("market_type", "crypto"),
                        doc=scrip,
                        matched_via="watchlist",
                    )
        return None

    def _resolve_with_llm(self, spoken_text: str) -> str | None:
        if not self.llm:
            return None
        known = [str(s.get("symbol", "")) for s in self.mongo.get_all_active() if s.get("symbol")]
        known_sample = ", ".join(known[:40])
        prompt = (
            "You map spoken trading commands to one ticker symbol.\n"
            f"Known symbols in database: {known_sample}\n"
            "Rules:\n"
            "- bitcoin, btc, or btcusdt -> BTCUSDT\n"
            "- ethereum, eth -> ETHUSDT\n"
            "- For Indian stocks use NSE symbol like RELIANCE (no .NS in output unless user said BSE).\n"
            "Reply with ONLY the symbol ticker, nothing else.\n"
            f"User said: {spoken_text}\n"
            "Symbol:"
        )
        try:
            answer = self.llm.answer(prompt).strip().upper()
        except Exception:
            return None
        answer = re.sub(r"[^A-Z0-9./-]", "", answer.split()[0] if answer.split() else "")
        return answer or None

    def _extract_token_from_speech(self, spoken_text: str) -> str | None:
        normalized = spoken_text.replace(",", " ").replace(".", " ").upper()
        tokens = [tok for tok in normalized.split() if tok]
        stop = {
            "ANALYZE", "ANALYSE", "CHECK", "SHOW", "TELL", "WHAT", "HOW", "FAR", "FROM",
            "LEVEL", "LEVELS", "TRIGGER", "PRICE", "THE", "IS", "ARE", "ME", "MY", "FOR",
            "OF", "A", "AN", "TO", "AND", "KRYPTO", "JARVIS", "HEY", "LIST", "ALL", "GET",
            "GIVE", "NIFTY", "STOCK", "STOCKS", "MOVED", "MOVE", "MOVER", "MOVERS", "TODAY",
            "THAN", "MORE", "PERCENT", "WHICH", "THAT", "THOSE", "THESE", "WITH", "ABOVE",
            "BELOW", "WATCHLIST", "CRYPTO", "MARKET", "DAILY",
            "PIN", "UNPIN", "STICK", "UNSTICK", "SCREEN", "SIDE", "WATCH",
            "NEWS", "HEADLINES", "HEADLINE", "ARTICLES", "ARTICLE", "LATEST",
        }
        for tok in tokens:
            if tok in stop:
                continue
            if tok.isdigit():
                continue
            if tok in CRYPTO_ALIASES or tok.endswith("USDT") or (tok.isalpha() and 3 <= len(tok) <= 12):
                return tok
        return None

    def resolve_from_speech(self, spoken_text: str) -> ResolvedSymbol | None:
        lower = spoken_text.lower()
        if any(
            phrase in lower
            for phrase in (
                "list all",
                "list nifty",
                "nifty 50",
                "nifty50",
                "moved more",
                "moved over",
                "watchlist",
                "movers",
                "headlines",
                "articles",
                "news of",
                "news for",
            )
        ):
            return None
        return self._resolve_from_speech_inner(spoken_text)

    def _resolve_from_speech_inner(self, spoken_text: str) -> ResolvedSymbol | None:
        token = self._extract_token_from_speech(spoken_text)
        if token:
            return self.resolve(token, spoken_context=spoken_text)
        if self.llm:
            llm_symbol = self._resolve_with_llm(spoken_text)
            if llm_symbol:
                return self.resolve(llm_symbol, spoken_context=spoken_text)
        return None

    def _normalize_token(self, raw: str) -> str:
        return re.sub(r"[^A-Z0-9]", "", raw.upper().strip())

    def _guess_market_type(self, symbol: str) -> str:
        upper = canonical_crypto_symbol(symbol)
        if upper.endswith("USDT") or upper in CRYPTO_ALIASES.values():
            return "crypto"
        if "/" in upper or (upper.endswith("USD") and not upper.endswith("USDT")):
            return "forex"
        return "indian_stock"
