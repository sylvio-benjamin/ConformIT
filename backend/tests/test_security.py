"""Tests unitaires du socle auth (hash + JWT) — sans base de données."""

from uuid import uuid4

import jwt
import pytest

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.config import JWT_SECRET


def test_password_roundtrip():
    hashed = hash_password("Secret123!")
    assert hashed != "Secret123!"
    assert verify_password("Secret123!", hashed)
    assert not verify_password("wrong", hashed)


def test_password_empty_rejected():
    assert verify_password("", "not-a-hash") is False
    assert verify_password("x", "") is False


def test_access_token_roundtrip():
    user_id = uuid4()
    org_id = uuid4()
    token, jti, expires = create_access_token(user_id, org_id, False)
    payload = decode_token(token, expected_type="access")
    assert payload["sub"] == str(user_id)
    assert payload["org"] == str(org_id)
    assert payload["jti"] == jti
    assert payload["adm"] is False
    assert expires is not None


def test_refresh_token_rejected_as_access():
    user_id = uuid4()
    token, _, _ = create_refresh_token(user_id)
    with pytest.raises(jwt.InvalidTokenError):
        decode_token(token, expected_type="access")


def test_tampered_token_rejected():
    user_id = uuid4()
    token, _, _ = create_access_token(user_id, None, True)
    with pytest.raises(jwt.InvalidTokenError):
        jwt.decode(token + "x", JWT_SECRET, algorithms=["HS256"])
