import pytest

from app.core.runtime_config import (
    DEV_JWT_FALLBACK,
    parse_cors_origins,
    resolve_jwt_secret,
    validate_runtime_config,
)


def test_cors_localhost_only_in_development():
    origins = parse_cors_origins("", "development")
    assert "http://localhost:3000" in origins
    assert parse_cors_origins("", "production") == []


def test_production_rejects_localhost_cors():
    with pytest.raises(RuntimeError, match="localhost"):
        validate_runtime_config(
            env="production",
            jwt_secret="a-long-explicit-production-secret",
            encryption_key="enc",
            cors_origins=["http://localhost:3000"],
        )


def test_production_requires_explicit_jwt_and_encryption():
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        validate_runtime_config(
            env="production",
            jwt_secret=DEV_JWT_FALLBACK,
            encryption_key="enc",
            cors_origins=["https://app.example.com"],
        )
    with pytest.raises(RuntimeError, match="ENCRYPTION_KEY"):
        validate_runtime_config(
            env="production",
            jwt_secret="a-long-explicit-production-secret",
            encryption_key="",
            cors_origins=["https://app.example.com"],
        )


def test_production_accepts_explicit_config():
    validate_runtime_config(
        env="production",
        jwt_secret="a-long-explicit-production-secret",
        encryption_key="enc",
        cors_origins=["https://app.example.com"],
    )


def test_jwt_default_only_in_development():
    assert resolve_jwt_secret("", "development") == DEV_JWT_FALLBACK
    assert resolve_jwt_secret("", "production") == ""
    assert resolve_jwt_secret("custom", "production") == "custom"
