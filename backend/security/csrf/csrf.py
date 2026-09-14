"""WebSecKit — CSRF double-submit cookie."""

from __future__ import annotations

import hmac
import secrets

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def create_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def verify_csrf(method: str, cookie_token: str | None, header_token: str | None) -> bool:
    if method.upper() in SAFE_METHODS:
        return True
    if not cookie_token or not header_token:
        return False
    return hmac.compare_digest(cookie_token, header_token)
