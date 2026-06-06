"""Web Push (VAPID) for morning Nifty 50 mover alerts."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")
from typing import Any
from zoneinfo import ZoneInfo

from pywebpush import WebPushException, webpush

from auth import decode_access_token
from market_helpers import compute_index_movers

IST = ZoneInfo("Asia/Kolkata")
PUSH_COLLECTION = "push_subscriptions"
_last_morning_push_date: str | None = None

def _load_vapid_private() -> str:
    raw = os.getenv("VAPID_PRIVATE_KEY", "").strip()
    if not raw:
        return ""
    if "\\n" in raw:
        return raw.replace("\\n", "\n")
    return raw


VAPID_PRIVATE_KEY = _load_vapid_private()
VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY", "").strip()
VAPID_SUBJECT = os.getenv("VAPID_SUBJECT", "mailto:bhushan@crypto-levels.local").strip()


def _push_coll(db):
    coll = db[PUSH_COLLECTION]
    coll.create_index("endpoint", unique=True)
    coll.create_index("user_id")
    return coll


def get_vapid_public_key() -> str:
    if not VAPID_PUBLIC_KEY:
        raise RuntimeError(
            "VAPID_PUBLIC_KEY not set. Run: python generate_vapid_keys.py"
        )
    return VAPID_PUBLIC_KEY


def _vapid_claims() -> dict[str, str]:
    return {"sub": VAPID_SUBJECT}


def _subscription_info(doc: dict[str, Any]) -> dict[str, Any]:
    return {
        "endpoint": doc["endpoint"],
        "keys": {
            "p256dh": doc["keys"]["p256dh"],
            "auth": doc["keys"]["auth"],
        },
    }


def save_subscription(
    db,
    subscription: dict[str, Any],
    user_id: str | None = None,
    user_agent: str | None = None,
) -> None:
    endpoint = subscription.get("endpoint")
    keys = subscription.get("keys") or {}
    if not endpoint or not keys.get("p256dh") or not keys.get("auth"):
        raise ValueError("Invalid push subscription")

    doc = {
        "endpoint": endpoint,
        "keys": {"p256dh": keys["p256dh"], "auth": keys["auth"]},
        "user_id": user_id,
        "user_agent": user_agent,
        "updated_at": datetime.utcnow(),
    }
    coll = _push_coll(db)
    coll.update_one(
        {"endpoint": endpoint},
        {
            "$set": doc,
            "$setOnInsert": {"created_at": datetime.utcnow()},
        },
        upsert=True,
    )


def remove_subscription(db, endpoint: str) -> bool:
    result = _push_coll(db).delete_one({"endpoint": endpoint})
    return result.deleted_count > 0


def send_push(
    subscription_doc: dict[str, Any],
    title: str,
    body: str,
    url: str = "/monitor",
    *,
    tag: str | None = None,
    event: str | None = None,
) -> None:
    if not VAPID_PRIVATE_KEY:
        raise RuntimeError("VAPID_PRIVATE_KEY not configured")

    payload: dict[str, Any] = {"title": title, "body": body, "url": url}
    if tag:
        payload["tag"] = tag
    if event:
        payload["event"] = event

    webpush(
        subscription_info=_subscription_info(subscription_doc),
        data=json.dumps(payload),
        vapid_private_key=VAPID_PRIVATE_KEY,
        vapid_claims=_vapid_claims(),
    )


def broadcast_push(
    db,
    title: str,
    body: str,
    url: str = "/monitor",
    *,
    user_id: str | None = None,
    tag: str | None = None,
    event: str | None = None,
) -> dict[str, int]:
    coll = _push_coll(db)
    query: dict[str, Any] = {}
    if user_id:
        query["user_id"] = user_id

    sent = 0
    failed = 0
    removed = 0

    for doc in coll.find(query):
        try:
            send_push(doc, title, body, url, tag=tag, event=event)
            sent += 1
        except WebPushException as exc:
            failed += 1
            status = getattr(exc, "response", None)
            code = status.status_code if status is not None else None
            if code in (404, 410):
                coll.delete_one({"_id": doc["_id"]})
                removed += 1
        except Exception:
            failed += 1

    return {"sent": sent, "failed": failed, "removed": removed}


def build_pin_alert_message(
    symbol: str,
    direction: str,
    ltp: float,
    alert_price: float,
    market_type: str = "crypto",
) -> tuple[str, str]:
    arrow = "above" if direction == "above" else "below"
    if market_type == "indian_stocks":
        price_s = f"₹{ltp:,.2f}"
        alert_s = f"₹{alert_price:,.2f}"
    else:
        price_s = f"{ltp:,.2f}"
        alert_s = f"{alert_price:,.2f}"
    title = f"{symbol} — price alert"
    body = f"{symbol} crossed {arrow} {alert_s} (now {price_s})"
    return title, body


def broadcast_pin_alert_push(
    db,
    *,
    symbol: str,
    direction: str,
    ltp: float,
    alert_price: float,
    market_type: str = "crypto",
) -> dict[str, int]:
    """Broadcast pin price alert to all push subscriptions."""
    title, body = build_pin_alert_message(symbol, direction, ltp, alert_price, market_type)
    tag = f"pin-alert-{symbol}-{direction}"
    return broadcast_push(
        db,
        title,
        body,
        url="/pins",
        tag=tag,
        event="pin_alert",
    )


def build_morning_nifty_message() -> tuple[str, str, dict[str, Any]]:
    """Title, body, full payload for morning push."""
    payload = compute_index_movers(
        "nifty50", 2.0, period="daily", direction="any", sort="desc"
    )
    movers = payload.get("movers") or []
    count = len(movers)

    title = f"Nifty 50 morning — {count} mover{'s' if count != 1 else ''} ≥2%"

    if count == 0:
        body = "No Nifty 50 stock moved 2% or more vs previous close."
    else:
        parts = []
        for m in movers[:12]:
            sym = m.get("symbol", "")
            pct = float(m.get("change_pct", 0))
            sign = "+" if pct >= 0 else ""
            parts.append(f"{sym} {sign}{pct:.1f}%")
        body = ", ".join(parts)
        if len(movers) > 12:
            body += f" (+{len(movers) - 12} more on site)"
        if len(body) > 240:
            body = body[:237] + "..."

    return title, body, payload


def run_morning_nifty_push(db) -> dict[str, Any]:
    """Scheduled 8 AM IST job."""
    global _last_morning_push_date

    today = datetime.now(IST).strftime("%Y-%m-%d")
    if _last_morning_push_date == today:
        return {"skipped": True, "reason": "already_sent_today"}

    title, body, payload = build_morning_nifty_message()
    stats = broadcast_push(db, title, body, url="/monitor")
    _last_morning_push_date = today

    return {
        "success": True,
        "date": today,
        "title": title,
        "body": body,
        "movers_count": payload.get("count", 0),
        **stats,
    }


def user_id_from_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    token = authorization.replace("Bearer ", "").strip()
    payload = decode_access_token(token)
    if not payload:
        return None
    return payload.get("user_id")


def morning_nifty_preview() -> dict[str, Any]:
    title, body, payload = build_morning_nifty_message()
    return {
        "success": True,
        "title": title,
        "body": body,
        "movers_count": payload.get("count", 0),
        "movers": payload.get("movers", [])[:30],
        "index_label": payload.get("index_label", "Nifty 50"),
    }
