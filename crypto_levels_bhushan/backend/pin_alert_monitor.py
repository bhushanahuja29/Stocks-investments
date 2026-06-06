"""Server-side price monitor — Web Push on pin alert cross."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from pin_alerts import (
    PIN_ALERTS_COLLECTION,
    has_notification_dedupe,
    log_notification,
)
from pin_market_hours import should_poll_pin

IST = ZoneInfo("Asia/Kolkata")


def _today_key() -> str:
    return datetime.now(IST).strftime("%Y-%m-%d")


def check_price_cross(
    doc: dict[str, Any],
    ltp: float,
) -> list[dict[str, Any]]:
    """Return list of fired alerts: {direction, alert_price}."""
    above = doc.get("alert_above")
    below = doc.get("alert_below")
    prev = doc.get("last_ltp")
    had_first = doc.get("had_first_quote", False)
    above_armed = doc.get("above_armed", True)
    below_armed = doc.get("below_armed", True)
    current = float(ltp)
    fired: list[dict[str, Any]] = []

    if not had_first:
        return fired

    if above is not None and above_armed and prev is not None:
        if float(prev) < float(above) <= current:
            fired.append({"direction": "above", "alert_price": float(above)})
            above_armed = False
    if current < (float(above) if above is not None else float("inf")):
        above_armed = True

    if below is not None and below_armed and prev is not None:
        if float(prev) > float(below) >= current:
            fired.append({"direction": "below", "alert_price": float(below)})
            below_armed = False
    if current > (float(below) if below is not None else 0):
        below_armed = True

    doc["_above_armed"] = above_armed
    doc["_below_armed"] = below_armed
    doc["_last_ltp"] = current
    return fired


def run_pin_alert_monitor(db) -> dict[str, Any]:
    from market_helpers import get_market_quote
    from push_notifications import broadcast_pin_alert_push

    coll = db[PIN_ALERTS_COLLECTION]
    pins = list(coll.find({"pinned": True}))
    checked = 0
    skipped_hours = 0
    crosses = 0
    pushes_sent = 0
    errors = 0

    for doc in pins:
        sym = doc.get("symbol", "")
        mtype = doc.get("market_type", "crypto")
        if not sym:
            continue

        if not should_poll_pin(sym, mtype):
            skipped_hours += 1
            continue

        if doc.get("alert_above") is None and doc.get("alert_below") is None:
            continue

        try:
            quote = get_market_quote(sym, mtype)
            ltp = quote.get("ltp")
            if ltp is None:
                continue
            checked += 1
            ltp_f = float(ltp)

            if not doc.get("had_first_quote"):
                coll.update_one(
                    {"_id": doc["_id"]},
                    {
                        "$set": {
                            "last_ltp": ltp_f,
                            "had_first_quote": True,
                            "above_armed": doc.get("alert_above") is None
                            or ltp_f < float(doc["alert_above"]),
                            "below_armed": doc.get("alert_below") is None
                            or ltp_f > float(doc["alert_below"]),
                        }
                    },
                )
                continue

            fired = check_price_cross(doc, ltp_f)
            update_fields: dict[str, Any] = {
                "last_ltp": doc.get("_last_ltp", ltp_f),
                "above_armed": doc.get("_above_armed", doc.get("above_armed", True)),
                "below_armed": doc.get("_below_armed", doc.get("below_armed", True)),
            }
            coll.update_one({"_id": doc["_id"]}, {"$set": update_fields})

            for alert in fired:
                direction = alert["direction"]
                alert_price = alert["alert_price"]
                day = _today_key()
                dedupe_key = f"pin_alert:{sym}:{direction}:{day}"
                if has_notification_dedupe(db, dedupe_key):
                    continue

                crosses += 1
                stats = broadcast_pin_alert_push(
                    db,
                    symbol=sym,
                    direction=direction,
                    ltp=ltp_f,
                    alert_price=alert_price,
                    market_type=mtype,
                )
                pushes_sent += stats.get("sent", 0)
                log_notification(
                    db,
                    dedupe_key=dedupe_key,
                    event="pin_alert",
                    symbol=sym,
                    title=f"{sym} alert",
                    body=f"{sym} crossed {direction} {alert_price:,.2f}",
                )

        except Exception:
            errors += 1

    return {
        "pins": len(pins),
        "checked": checked,
        "skipped_hours": skipped_hours,
        "crosses": crosses,
        "pushes_sent": pushes_sent,
        "errors": errors,
    }
