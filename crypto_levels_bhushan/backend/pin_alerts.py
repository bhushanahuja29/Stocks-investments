"""Global pin alerts stored in MongoDB — synced from Jarvis desktop."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

from pin_market_hours import pin_session_status, should_poll_pin

PIN_ALERTS_COLLECTION = "pin_alerts"
NOTIFICATION_LOGS_COLLECTION = "notification_logs"


def ensure_pin_indexes(db) -> None:
    coll = db[PIN_ALERTS_COLLECTION]
    coll.create_index("symbol", unique=True)
    coll.create_index("pinned")
    logs = db[NOTIFICATION_LOGS_COLLECTION]
    logs.create_index("dedupe_key", unique=True)
    logs.create_index("created_at")


def _normalize_symbol(symbol: str) -> str:
    return symbol.upper().strip()


def _normalize_market_type(market_type: str) -> str:
    m = (market_type or "crypto").strip().lower()
    if m in ("indian_stock", "indian_stocks"):
        return "indian_stocks"
    if m in ("forex", "commodity"):
        return "forex"
    return "crypto"


def _parse_alert(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def verify_jarvis_key(header_value: str | None) -> bool:
    expected = os.getenv("JARVIS_SYNC_KEY", "").strip()
    if not expected:
        return False
    return (header_value or "").strip() == expected


def upsert_pin(
    db,
    symbol: str,
    market_type: str,
    *,
    alert_above: float | None = None,
    alert_below: float | None = None,
    created_by: str = "web",
) -> dict[str, Any]:
    sym = _normalize_symbol(symbol)
    mtype = _normalize_market_type(market_type)
    now = datetime.utcnow()
    coll = db[PIN_ALERTS_COLLECTION]

    existing = coll.find_one({"symbol": sym})
    update: dict[str, Any] = {
        "symbol": sym,
        "market_type": mtype,
        "alert_above": alert_above,
        "alert_below": alert_below,
        "pinned": True,
        "updated_at": now,
        "created_by": created_by,
    }
    if existing is None:
        update.update(
            {
                "last_ltp": None,
                "above_armed": True,
                "below_armed": True,
                "had_first_quote": False,
                "alert_ringing": False,
                "alert_direction": None,
                "alert_trigger_price": None,
                "created_at": now,
            }
        )
    elif (
        alert_above != existing.get("alert_above")
        or alert_below != existing.get("alert_below")
    ):
        # Re-baseline so a new threshold fires even if price is already past it.
        update["above_armed"] = True
        update["below_armed"] = True
        update["had_first_quote"] = False
        update["last_ltp"] = None
        update["alert_ringing"] = False
        update["alert_direction"] = None
        update["alert_trigger_price"] = None

    coll.update_one({"symbol": sym}, {"$set": update}, upsert=True)
    doc = coll.find_one({"symbol": sym})
    return _serialize_pin(doc)


def delete_pin(db, symbol: str) -> bool:
    sym = _normalize_symbol(symbol)
    result = db[PIN_ALERTS_COLLECTION].delete_one({"symbol": sym})
    return result.deleted_count > 0


def sync_pins(
    db,
    entries: list[dict[str, Any]],
    *,
    created_by: str = "jarvis",
) -> dict[str, Any]:
    """Replace global pin list with entries from Jarvis."""
    coll = db[PIN_ALERTS_COLLECTION]
    incoming_symbols: set[str] = set()
    upserted = 0

    for item in entries:
        sym = _normalize_symbol(str(item.get("symbol", "")))
        if not sym:
            continue
        incoming_symbols.add(sym)
        upsert_pin(
            db,
            sym,
            str(item.get("market_type", "crypto")),
            alert_above=_parse_alert(item.get("alert_above")),
            alert_below=_parse_alert(item.get("alert_below")),
            created_by=created_by,
        )
        upserted += 1

    removed = 0
    for doc in coll.find({}):
        if doc["symbol"] not in incoming_symbols:
            coll.delete_one({"_id": doc["_id"]})
            removed += 1

    return {"upserted": upserted, "removed": removed, "count": len(incoming_symbols)}


def _serialize_pin(doc: dict[str, Any] | None) -> dict[str, Any] | None:
    if not doc:
        return None
    out = {
        "symbol": doc.get("symbol"),
        "market_type": doc.get("market_type"),
        "alert_above": doc.get("alert_above"),
        "alert_below": doc.get("alert_below"),
        "pinned": doc.get("pinned", True),
        "last_ltp": doc.get("last_ltp"),
        "session_status": pin_session_status(
            doc.get("symbol", ""), doc.get("market_type", "crypto")
        ),
        "polling_active": should_poll_pin(
            doc.get("symbol", ""), doc.get("market_type", "crypto")
        ),
        "alert_ringing": bool(doc.get("alert_ringing")),
        "alert_direction": doc.get("alert_direction"),
        "alert_trigger_price": doc.get("alert_trigger_price"),
        "updated_at": doc.get("updated_at").isoformat() if doc.get("updated_at") else None,
        "created_by": doc.get("created_by"),
    }
    return out


def list_pins(db, *, attach_quotes: bool = True) -> list[dict[str, Any]]:
    from market_helpers import get_market_quote

    coll = db[PIN_ALERTS_COLLECTION]
    pins = list(coll.find({"pinned": True}).sort("symbol", 1))
    result: list[dict[str, Any]] = []

    for doc in pins:
        row = _serialize_pin(doc) or {}
        if attach_quotes:
            try:
                quote = get_market_quote(doc["symbol"], doc.get("market_type", "crypto"))
                row["quote"] = quote
            except Exception:
                row["quote"] = None
        result.append(row)

    return result


def stop_pin_alert(db, symbol: str) -> bool:
    """Silence repeating alerts until price re-arms or thresholds change."""
    sym = _normalize_symbol(symbol)
    coll = db[PIN_ALERTS_COLLECTION]
    result = coll.update_one(
        {"symbol": sym},
        {
            "$set": {
                "alert_ringing": False,
                "alert_direction": None,
                "alert_trigger_price": None,
                "updated_at": datetime.utcnow(),
            }
        },
    )
    return result.matched_count > 0


def set_pin_ringing(
    db,
    symbol: str,
    *,
    direction: str,
    trigger_price: float,
) -> None:
    sym = _normalize_symbol(symbol)
    db[PIN_ALERTS_COLLECTION].update_one(
        {"symbol": sym},
        {
            "$set": {
                "alert_ringing": True,
                "alert_direction": direction,
                "alert_trigger_price": trigger_price,
                "updated_at": datetime.utcnow(),
            }
        },
    )


def has_notification_dedupe(db, dedupe_key: str) -> bool:
    return db[NOTIFICATION_LOGS_COLLECTION].find_one({"dedupe_key": dedupe_key}) is not None


def log_notification(
    db,
    *,
    dedupe_key: str,
    event: str,
    symbol: str,
    title: str,
    body: str,
) -> None:
    db[NOTIFICATION_LOGS_COLLECTION].insert_one(
        {
            "dedupe_key": dedupe_key,
            "event": event,
            "symbol": symbol,
            "title": title,
            "body": body,
            "created_at": datetime.utcnow(),
        }
    )
