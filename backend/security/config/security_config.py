"""WebSecKit — FastAPI security configuration.

Aligné sur ConformIT : JWT/cookies existants restent la source d'auth.
CSRF / CAPTCHA / MFA désactivés jusqu'à câblage front explicite.
Le rate limit métier (login / analyse) reste dans app.core.rate_limit.
"""

from __future__ import annotations

import os

PROJECT_TYPE = "saas"
FRAMEWORK = "fastapi"

ENABLED = {
    "headers": True,
    "cors": False,  # CORS Starlette déjà câblé dans app.main
    "https": True,
    "rateLimit": False,  # conserve app.core.rate_limit (login / analyse)
    "authentication": True,
    "authorization": True,
    "csrf": False,  # cookies JWT déjà en place ; CSRF = étape front séparée
    "captcha": False,
    "uploads": True,
    "webhooks": False,  # Stripe laissé tel quel (hors WebSecKit)
    "mfa": False,
    "payments": False,  # Stripe existant non remplacé
}

# Back-compat alias used by middleware.
MODULES = {
    "authentication": ENABLED["authentication"],
    "authorization": ENABLED["authorization"],
    "rateLimiting": ENABLED["rateLimit"],
    "captcha": ENABLED["captcha"],
    "fileUploads": ENABLED["uploads"],
    "payments": ENABLED["payments"],
    "api": True,
    "csrf": ENABLED["csrf"],
    "mfa": ENABLED["mfa"],
    "adminPanel": True,
}


def _cors_origins() -> list[str]:
    raw = os.getenv("CORS_ALLOWED_ORIGINS") or os.getenv("CORS_ORIGINS") or "http://localhost:3000"
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


CORS_ALLOWED_ORIGINS = _cors_origins()

HSTS_MAX_AGE = 15_552_000
MIN_PASSWORD_LENGTH = 12
SESSION_IDLE_MS = 15 * 60 * 1000
SESSION_ABSOLUTE_MS = 8 * 60 * 60 * 1000
PASSWORD_RESET_TTL_MS = 30 * 60 * 1000
MAX_LOGIN_ATTEMPTS = 8
LOCKOUT_MS = 15 * 60 * 1000
RATE_LIMITS = {
    "global": {"window_ms": 60_000, "max": 300},
    "ip": {"window_ms": 60_000, "max": 120},
    "user": {"window_ms": 60_000, "max": 200},
    "login": {"window_ms": 15 * 60_000, "max": 8},
    "api": {"window_ms": 60_000, "max": 60},
}
# Aligné sur UploadFileValidation.MAX_FILE_SIZE (10 Mo).
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".pdf", ".csv", ".xls", ".xlsx"}
MAX_BODY_BYTES = 64 * 1024
MAX_PAGE_SIZE = 100
WEBHOOK_SKEW_MS = 5 * 60 * 1000
