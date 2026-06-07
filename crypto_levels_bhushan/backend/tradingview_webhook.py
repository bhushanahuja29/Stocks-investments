"""TradingView webhook — parse alerts, store history, broadcast Web Push."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from pin_alerts import has_notification_dedupe, log_notification

IST = ZoneInfo("Asia/Kolkata")
TV_ALERTS_COLLECTION = "tradingview_alerts"


def ensure_tv_alert_indexes(db) -> None:
    coll = db[TV_ALERTS_COLLECTION]
    coll.create_index([("created_at", -1)])


def verify_tradingview_secret(query_secret: str | None) -> bool:
    expected = os.getenv("TRADINGVIEW_WEBHOOK_SECRET", "").strip()
    if not expected:
        return False
    return (query_secret or "").strip() == expected


def _normalize_market_type(exchange: str) -> str:
    ex = (exchange or "").upper().strip()
    if ex in ("NSE", "BSE", "NSEI"):
        return "indian_stocks"
    if ex in ("BINANCE", "BYBIT", "COINBASE"):
        return "crypto"
    if ex in ("OANDA", "FX", "FOREX"):
        return "forex"
    return "crypto"


def normalize_ticker(ticker: str) -> tuple[str, str]:
    """NSE:RELIANCE -> (RELIANCE, indian_stocks); BINANCE:BTCUSDT -> (BTCUSDT, crypto)."""
    raw = (ticker or "").strip()
    if not raw:
        return "", "crypto"

    if ":" in raw:
        exchange, symbol = raw.split(":", 1)
        sym = symbol.upper().strip().replace(".NS", "").replace(".BO", "")
        return sym, _normalize_market_type(exchange)

    sym = raw.upper().strip().replace(".NS", "").replace(".BO", "")
    return sym, "crypto"


def _parse_price(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None


def parse_payload(body: bytes, content_type: str | None) -> dict[str, Any]:
    """Parse TradingView POST body (JSON or plain text)."""
    text = body.decode("utf-8", errors="replace").strip()
    if not text:
        return {"raw": "", "symbol": "", "market_type": "crypto"}

    ct = (content_type or "").lower()
    if "json" in ct or text.startswith("{"):
        try:
            data = json.loads(text)
            if isinstance(data, dict):
                ticker = data.get("ticker") or data.get("symbol") or ""
                symbol, market_type = normalize_ticker(str(ticker))
                return {
                    "raw": text,
                    "ticker": str(ticker),
                    "symbol": symbol,
                    "market_type": market_type,
                    "price": _parse_price(data.get("price") or data.get("close")),
                    "action": str(data.get("action") or data.get("side") or "").strip() or None,
                    "message": str(data.get("message") or data.get("msg") or "").strip() or None,
                    "interval": str(data.get("interval") or data.get("timeframe") or "").strip() or None,
                    "alert_time": str(data.get("time") or data.get("timenow") or "").strip() or None,
                }
        except json.JSONDecodeError:
            pass

    symbol, market_type = normalize_ticker(text)
    price_match = re.search(r"(\d[\d,]*\.?\d*)", text)
    price = _parse_price(price_match.group(1)) if price_match else None
    return {
        "raw": text,
        "ticker": text,
        "symbol": symbol,
        "market_type": market_type,
        "price": price,
        "action": None,
        "message": text,
        "interval": None,
        "alert_time": None,
    }


def _dedupe_key(symbol: str, action: str | None, price: float | None) -> str:
    now = datetime.now(IST)
    minute = now.strftime("%Y-%m-%dT%H:%M")
    act = action or "alert"
    price_s = f"{price:g}" if price is not None else "na"
    sym = symbol or "unknown"
    return f"tv_alert:{sym}:{act}:{price_s}:{minute}"


def _serialize_alert(doc: dict[str, Any]) -> dict[str, Any]:
    created = doc.get("created_at")
    return {
        "id": str(doc.get("_id", "")),
        "symbol": doc.get("symbol"),
        "ticker": doc.get("ticker"),
        "market_type": doc.get("market_type"),
        "price": doc.get("price"),
        "action": doc.get("action"),
        "message": doc.get("message"),
        "interval": doc.get("interval"),
        "alert_time": doc.get("alert_time"),
        "created_at": created.isoformat() if created else None,
    }


def store_alert(db, parsed: dict[str, Any]) -> dict[str, Any]:
    now = datetime.utcnow()
    doc = {
        "ticker": parsed.get("ticker"),
        "symbol": parsed.get("symbol") or "UNKNOWN",
        "market_type": parsed.get("market_type", "crypto"),
        "price": parsed.get("price"),
        "action": parsed.get("action"),
        "message": parsed.get("message"),
        "interval": parsed.get("interval"),
        "alert_time": parsed.get("alert_time"),
        "raw": parsed.get("raw"),
        "created_at": now,
    }
    result = db[TV_ALERTS_COLLECTION].insert_one(doc)
    doc["_id"] = result.inserted_id
    return _serialize_alert(doc)


def list_alerts(db, *, limit: int = 50) -> list[dict[str, Any]]:
    limit = max(1, min(limit, 200))
    cursor = db[TV_ALERTS_COLLECTION].find().sort("created_at", -1).limit(limit)
    return [_serialize_alert(doc) for doc in cursor]


def handle_tradingview_webhook(db, parsed: dict[str, Any]) -> dict[str, Any]:
    """Store alert, dedupe push, broadcast to subscribers."""
    from push_notifications import broadcast_tradingview_alert_push

    alert = store_alert(db, parsed)
    symbol = alert.get("symbol") or "UNKNOWN"
    action = alert.get("action")
    price = alert.get("price")
    message = alert.get("message")
    market_type = alert.get("market_type") or "crypto"

    dedupe_key = _dedupe_key(symbol, action, price)
    push_stats = {"sent": 0, "failed": 0, "removed": 0, "skipped": False}

    if has_notification_dedupe(db, dedupe_key):
        push_stats["skipped"] = True
    else:
        title = f"TV Alert — {symbol}"
        body = message or f"{action or 'Alert'}" + (f" @ {price:g}" if price is not None else "")
        push_stats = broadcast_tradingview_alert_push(
            db,
            symbol=symbol,
            action=action,
            price=price,
            message=message,
            market_type=market_type,
        )
        log_notification(
            db,
            dedupe_key=dedupe_key,
            event="tradingview_alert",
            symbol=symbol,
            title=title,
            body=body,
        )

    return {
        "success": True,
        "alert_id": alert.get("id"),
        "alert": alert,
        "push": push_stats,
    }
