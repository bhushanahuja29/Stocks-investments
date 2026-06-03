from __future__ import annotations

from typing import Any


def format_news_speech(payload: dict[str, Any], spoken_limit: int = 5) -> str:
    sym = payload.get("symbol", "")
    label = payload.get("month_label", "")
    count = payload.get("count", 0)
    articles = payload.get("articles") or []

    if count == 0:
        warnings = payload.get("warnings") or []
        extra = warnings[0] if warnings else "Try a more recent month."
        return f"No headlines found for {sym} in {label}. {extra}"

    lines = [f"{count} headline{'s' if count != 1 else ''} for {sym} in {label}."]
    for i, art in enumerate(articles[:spoken_limit]):
        title = art.get("title", "Untitled")
        src = art.get("source", "")
        lines.append(f"{i + 1}. {title}" + (f" ({src})" if src else ""))

    if count > spoken_limit:
        lines.append(f"And {count - spoken_limit} more in the activity log with links.")

    warnings = payload.get("warnings") or []
    if warnings and count > 0:
        lines.append("Note: Yahoo only keeps recent articles; older months may be incomplete.")

    return " ".join(lines)


def format_news_log(payload: dict[str, Any]) -> str:
    articles = payload.get("articles") or []
    lines = [
        f"News — {payload.get('symbol')} — {payload.get('month_label')} "
        f"({payload.get('count', 0)} articles)",
        f"Sources: {', '.join(payload.get('sources_used') or [])}",
    ]
    for w in payload.get("warnings") or []:
        lines.append(f"Warning: {w}")
    lines.append("")
    for i, art in enumerate(articles, 1):
        lines.append(f"{i}. {art.get('title', '')}")
        if art.get("published_at"):
            lines.append(f"   Date: {art['published_at']}")
        lines.append(f"   {art.get('url', '')}")
        lines.append("")
    return "\n".join(lines)
