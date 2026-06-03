"""NSE index constituent lists for Krypto market scans (refresh periodically)."""

from __future__ import annotations

import re
from typing import Any

from nifty50_data import NIFTY_50_STOCKS

# Bank Nifty — 12 banking stocks (NSE Bank Nifty index)
BANK_NIFTY_STOCKS: list[dict[str, str]] = [
    {"symbol": "HDFCBANK", "name": "HDFC Bank"},
    {"symbol": "ICICIBANK", "name": "ICICI Bank"},
    {"symbol": "AXISBANK", "name": "Axis Bank"},
    {"symbol": "SBIN", "name": "State Bank of India"},
    {"symbol": "KOTAKBANK", "name": "Kotak Mahindra Bank"},
    {"symbol": "INDUSINDBK", "name": "IndusInd Bank"},
    {"symbol": "BANKBARODA", "name": "Bank of Baroda"},
    {"symbol": "PNB", "name": "Punjab National Bank"},
    {"symbol": "FEDERALBNK", "name": "Federal Bank"},
    {"symbol": "IDFCFIRSTB", "name": "IDFC First Bank"},
    {"symbol": "AUBANK", "name": "AU Small Finance Bank"},
    {"symbol": "BANDHANBNK", "name": "Bandhan Bank"},
]

# Fin Nifty — banks + major NBFCs / financials
FIN_NIFTY_STOCKS: list[dict[str, str]] = [
    *BANK_NIFTY_STOCKS,
    {"symbol": "BAJFINANCE", "name": "Bajaj Finance"},
    {"symbol": "BAJAJFINSV", "name": "Bajaj Finserv"},
    {"symbol": "CHOLAFIN", "name": "Cholamandalam Investment"},
    {"symbol": "SHRIRAMFIN", "name": "Shriram Finance"},
    {"symbol": "SBILIFE", "name": "SBI Life Insurance"},
    {"symbol": "HDFCLIFE", "name": "HDFC Life Insurance"},
    {"symbol": "ICICIGI", "name": "ICICI Lombard"},
    {"symbol": "ICICIPRULI", "name": "ICICI Prudential Life"},
    {"symbol": "MUTHOOTFIN", "name": "Muthoot Finance"},
    {"symbol": "PFC", "name": "Power Finance Corporation"},
    {"symbol": "RECLTD", "name": "REC Limited"},
    {"symbol": "LICI", "name": "Life Insurance Corporation"},
]

INDEX_REGISTRY: dict[str, dict[str, Any]] = {
    "nifty50": {
        "label": "Nifty 50",
        "constituents": NIFTY_50_STOCKS,
    },
    "banknifty": {
        "label": "Bank Nifty",
        "constituents": BANK_NIFTY_STOCKS,
    },
    "finnifty": {
        "label": "Fin Nifty",
        "constituents": FIN_NIFTY_STOCKS,
    },
}

_VALID_INDEX_IDS = frozenset(INDEX_REGISTRY.keys())


def normalize_index_id(index: str | None) -> str:
    if not index:
        return "nifty50"
    key = index.lower().strip().replace(" ", "").replace("_", "").replace("-", "")
    aliases = {
        "nifty50": "nifty50",
        "nifty": "nifty50",
        "n50": "nifty50",
        "banknifty": "banknifty",
        "bnifty": "banknifty",
        "bank": "banknifty",
        "finnifty": "finnifty",
        "fnifty": "finnifty",
        "fin": "finnifty",
    }
    return aliases.get(key, key if key in _VALID_INDEX_IDS else "nifty50")


def get_constituents(index_id: str) -> tuple[str, str, list[dict[str, str]]]:
    """Return (index_id, display_label, constituents)."""
    idx = normalize_index_id(index_id)
    entry = INDEX_REGISTRY[idx]
    return idx, entry["label"], list(entry["constituents"])


def resolve_index_from_text(text: str) -> tuple[str, str]:
    """Map natural language to index id + label."""
    lower = text.lower()
    if re.search(r"\b(fin\s*nifty|finnifty|financial\s+nifty|fin\s+service)\b", lower):
        return get_constituents("finnifty")[:2]
    if re.search(
        r"\b(bank\s*nifty|banknifty|banking\s+stocks?|bank\s+stocks?|indian\s+bank|banks?\s+that)\b",
        lower,
    ):
        return get_constituents("banknifty")[:2]
    if re.search(r"\b(nifty\s*50|nifty50|n50)\b", lower):
        return get_constituents("nifty50")[:2]
    return get_constituents("nifty50")[:2]


def list_indices() -> list[dict[str, Any]]:
    return [
        {"id": idx, "label": meta["label"], "count": len(meta["constituents"])}
        for idx, meta in INDEX_REGISTRY.items()
    ]
