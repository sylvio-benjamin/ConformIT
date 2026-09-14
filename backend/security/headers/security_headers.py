"""WebSecKit — HTTP security headers for Starlette/FastAPI."""

from __future__ import annotations

import os

from ..config.security_config import HSTS_MAX_AGE


def build_csp() -> str:
    return (
        "default-src 'self'; base-uri 'self'; form-action 'self'; "
        "frame-ancestors 'none'; object-src 'none'; script-src 'self'; "
        "style-src 'self'; img-src 'self' data:; connect-src 'self'; "
        "font-src 'self'; frame-src 'none'; upgrade-insecure-requests"
    )


def security_header_map(is_production: bool | None = None) -> dict[str, str]:
    if is_production is None:
        is_production = os.getenv("ENV", os.getenv("NODE_ENV", "development")) == "production"
    headers = {
        "Content-Security-Policy": build_csp(),
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
        "Cross-Origin-Opener-Policy": "same-origin",
        "Cross-Origin-Resource-Policy": "same-origin",
        "X-DNS-Prefetch-Control": "off",
        "X-Permitted-Cross-Domain-Policies": "none",
    }
    if is_production:
        headers["Strict-Transport-Security"] = f"max-age={HSTS_MAX_AGE}; includeSubDomains; preload"
    return headers
