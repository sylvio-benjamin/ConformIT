"""Validation de configuration au démarrage — pas de prod ambiguë."""

from __future__ import annotations

DEV_JWT_FALLBACK = "dev-only-insecure-secret"
LOCAL_ORIGIN_MARKERS = ("localhost", "127.0.0.1", "0.0.0.0", "[::1]")


def parse_cors_origins(raw: str, env: str) -> list[str]:
    items = [item.strip() for item in (raw or "").split(",") if item.strip()]
    if env == "development":
        for extra in ("http://localhost:3000", "http://127.0.0.1:3000"):
            if extra not in items:
                items.append(extra)
    return items


def resolve_jwt_secret(raw: str, env: str) -> str:
    value = (raw or "").strip()
    if value:
        return value
    if env == "development":
        return DEV_JWT_FALLBACK
    return ""


def validate_runtime_config(
    *,
    env: str,
    jwt_secret: str,
    encryption_key: str,
    cors_origins: list[str],
) -> None:
    errors: list[str] = []
    if env == "development":
        if "*" in cors_origins:
            errors.append("CORS * interdit")
    else:
        if not jwt_secret or jwt_secret == DEV_JWT_FALLBACK:
            errors.append("JWT_SECRET obligatoire et explicite hors development")
        if not encryption_key:
            errors.append("ENCRYPTION_KEY obligatoire hors development")
        if not cors_origins:
            errors.append("CORS_ORIGINS obligatoire hors development")
        for origin in cors_origins:
            lowered = origin.lower()
            if origin == "*" or any(marker in lowered for marker in LOCAL_ORIGIN_MARKERS):
                errors.append(f"origine interdite hors development: {origin}")
    if errors:
        raise RuntimeError("Configuration invalide : " + " ; ".join(errors))


def validate_storage_config(
    *,
    storage_backend: str = "local",
    s3_bucket: str = "",
    s3_access_key: str = "",
    s3_secret_key: str = "",
    s3_endpoint: str = "",
) -> None:
    name = (storage_backend or "local").strip().lower()
    if name in {"local", "memory", ""}:
        return
    errors: list[str] = []
    if name in {"s3", "r2"}:
        if not (s3_bucket or "").strip():
            errors.append("S3_BUCKET obligatoire si STORAGE_BACKEND=s3 ou r2")
        if not (s3_access_key or "").strip() or not (s3_secret_key or "").strip():
            errors.append("S3_ACCESS_KEY et S3_SECRET_KEY obligatoires si STORAGE_BACKEND=s3 ou r2")
        if name == "r2" and not (s3_endpoint or "").strip():
            errors.append("S3_ENDPOINT obligatoire si STORAGE_BACKEND=r2 (https://<ACCOUNT_ID>.r2.cloudflarestorage.com)")
    else:
        errors.append(f"STORAGE_BACKEND inconnu: {name}")
    if errors:
        raise RuntimeError("Configuration invalide : " + " ; ".join(errors))
