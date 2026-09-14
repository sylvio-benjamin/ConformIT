"""WebSecKit — basic bot heuristics."""

from __future__ import annotations

HONEYPOT_FIELD = "website"


def is_suspicious_user_agent(user_agent: str | None) -> bool:
    ua = (user_agent or "").strip()
    return not ua or len(ua) > 512


def honeypot_triggered(body: dict[str, object], field: str = HONEYPOT_FIELD) -> bool:
    value = body.get(field)
    if isinstance(value, str):
        return bool(value.strip())
    return bool(value)
