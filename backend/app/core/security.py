"""Hash mot de passe, JWT, cookies de session."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

import bcrypt
import jwt

from app.config import (
    COOKIE_SECURE,
    ENV,
    JWT_ACCESS_MINUTES,
    JWT_REFRESH_DAYS,
    JWT_SECRET,
)

ACCESS_COOKIE = "da_access"
REFRESH_COOKIE = "da_refresh"
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    if not password or not password_hash:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def new_reset_token() -> str:
    return secrets.token_urlsafe(32)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(
    user_id: UUID,
    organization_id: Optional[UUID],
    is_platform_admin: bool,
    jti: Optional[str] = None,
) -> tuple[str, str, datetime]:
    token_jti = jti or str(uuid4())
    expires = _utcnow() + timedelta(minutes=JWT_ACCESS_MINUTES)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "org": str(organization_id) if organization_id else None,
        "adm": bool(is_platform_admin),
        "jti": token_jti,
        "typ": "access",
        "exp": expires,
        "iat": _utcnow(),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)
    return token, token_jti, expires


def create_refresh_token(user_id: UUID, jti: Optional[str] = None) -> tuple[str, str, datetime]:
    token_jti = jti or str(uuid4())
    expires = _utcnow() + timedelta(days=JWT_REFRESH_DAYS)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "jti": token_jti,
        "typ": "refresh",
        "exp": expires,
        "iat": _utcnow(),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)
    return token, token_jti, expires


def decode_token(token: str, expected_type: str = "access") -> dict[str, Any]:
    payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
    if payload.get("typ") != expected_type:
        raise jwt.InvalidTokenError("Type de jeton invalide")
    return payload


def set_auth_cookies(response, access: str, refresh: str) -> None:
    common = {
        "httponly": True,
        "samesite": "lax",
        "secure": COOKIE_SECURE,
        "path": "/",
    }
    response.set_cookie(
        ACCESS_COOKIE,
        access,
        max_age=JWT_ACCESS_MINUTES * 60,
        **common,
    )
    response.set_cookie(
        REFRESH_COOKIE,
        refresh,
        max_age=JWT_REFRESH_DAYS * 24 * 3600,
        **common,
    )


def clear_auth_cookies(response) -> None:
    response.delete_cookie(ACCESS_COOKIE, path="/")
    response.delete_cookie(REFRESH_COOKIE, path="/")


def assert_jwt_configured() -> None:
    from app.config import CORS_ORIGINS, ENCRYPTION_KEY
    from app.core.runtime_config import validate_runtime_config

    validate_runtime_config(
        env=ENV,
        jwt_secret=JWT_SECRET,
        encryption_key=ENCRYPTION_KEY,
        cors_origins=CORS_ORIGINS,
    )
