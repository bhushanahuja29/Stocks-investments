from __future__ import annotations

import math
from typing import Any


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


def _movers_meta(payload: dict[str, Any], *, label: str | None = None) -> dict[str, Any]:
    movers = _clean_movers(payload.get("movers") or [])
    min_pct = payload.get("min_pct", 2)
    period = payload.get("period", "daily")
    direction = payload.get("direction", "any")
    label = label or payload.get("index_label") or "Nifty 50"
    gainers = [m for m in movers if float(m["change_pct"]) > 0]
    losers = [m for m in movers if float(m["change_pct"]) < 0]

    dir_note = ""
    if direction == "up":
        dir_note = " (gainers only)"
    elif direction == "down":
        dir_note = " (losers only)"

    return {
        "movers": movers,
        "label": label,
        "count": len(movers),
        "gainers": len(gainers),
        "losers": len(losers),
        "min_pct": min_pct,
        "period": period,
        "dir_note": dir_note,
        "sort": payload.get("sort", "desc"),
    }


def format_movers_speech(payload: dict[str, Any], *, label: str | None = None, spoken_limit: int = 5) -> str:
    """Short TTS summary — not the full mover list."""
    meta = _movers_meta(payload, label=label)
    movers = meta["movers"]
    label = meta["label"]

    if meta["count"] == 0:
        return (
            f"No {label} stocks match {meta['min_pct']}% move filter "
            f"({meta['period']}{meta['dir_note']})."
        )

    lines = [
        f"{meta['count']} {label} stocks: {meta['gainers']} up and {meta['losers']} down.",
    ]
    for idx, row in enumerate(movers[:spoken_limit], start=1):
        name = row.get("name") or row["symbol"]
        pct = float(row["change_pct"])
        sign = "+" if pct > 0 else ""
        lines.append(f"{idx}. {name}: {sign}{pct:.2f}%.")

    if meta["count"] > spoken_limit:
        lines.append(f"Full table with all {meta['count']} stocks is on screen.")

    return " ".join(lines)


def movers_table_payload(payload: dict[str, Any], *, label: str | None = None) -> dict[str, Any]:
    meta = _movers_meta(payload, label=label)
    title = (
        f"{meta['label']} — {meta['count']} stocks "
        f"({meta['gainers']} up, {meta['losers']} down)"
    )
    rows = [
        {
            "symbol": row["symbol"],
            "name": row.get("name") or row["symbol"],
            "price": row["price"],
            "change_pct": row["change_pct"],
        }
        for row in meta["movers"]
    ]
    return {
        "view": "movers_table",
        "title": title,
        "summary": f"{meta['gainers']} up, {meta['losers']} down",
        "movers": rows,
    }
