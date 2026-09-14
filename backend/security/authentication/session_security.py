"""WebSecKit — session lifetime helpers."""

from __future__ import annotations

import os
import secrets
import time

from ..config.security_config import SESSION_ABSOLUTE_MS, SESSION_IDLE_MS


def create_session_id() -> str:
    return secrets.token_urlsafe(32)


def is_session_expired(created_at_ms: float, last_seen_at_ms: float, now_ms: float | None = None) -> bool:
    now = time.time() * 1000 if now_ms is None else now_ms
    if now - created_at_ms > SESSION_ABSOLUTE_MS:
        return True
    if now - last_seen_at_ms > SESSION_IDLE_MS:
        return True
    return False


def session_cookie(session_id: str, is_production: bool | None = None) -> str:
    if is_production is None:
        is_production = os.getenv("ENV") == "production"
    name = "__Host-session" if is_production else "session"
    parts = [f"{name}={session_id}", "HttpOnly", "Path=/", "SameSite=Lax"]
    if is_production:
        parts.append("Secure")
    return "; ".join(parts)
