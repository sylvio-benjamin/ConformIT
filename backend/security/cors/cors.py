"""WebSecKit — CORS allowlist."""

from __future__ import annotations

from ..config.security_config import CORS_ALLOWED_ORIGINS

ALLOW_HEADERS = (
    "Content-Type,Authorization,X-CSRF-Token,X-Request-Id,"
    "X-DocAnalyse-Secret,X-Requested-With"
)


def resolve_cors(request_origin: str | None) -> tuple[bool, dict[str, str]]:
    origin = (request_origin or "").strip() or None
    if origin is None or origin not in CORS_ALLOWED_ORIGINS:
        return False, {}
    return True, {
        "Access-Control-Allow-Origin": origin,
        "Vary": "Origin",
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "GET,POST,PUT,PATCH,DELETE,OPTIONS",
        "Access-Control-Allow-Headers": ALLOW_HEADERS,
        "Access-Control-Max-Age": "600",
    }
