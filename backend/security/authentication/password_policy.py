"""WebSecKit — password policy."""

from __future__ import annotations

from ..config.security_config import MIN_PASSWORD_LENGTH

_COMMON = {"password", "password123", "123456789012", "qwertyuiop", "letmein12345"}


def validate_password(password: str, extra_banned: list[str] | None = None) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if len(password) < MIN_PASSWORD_LENGTH:
        errors.append(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
    if len(password) > 256:
        errors.append("Password is too long.")
    if not any(c.islower() for c in password) or not any(c.isupper() for c in password) or not any(c.isdigit() for c in password):
        errors.append("Password must include upper, lower, and numeric characters.")
    lowered = password.lower()
    banned = extra_banned or []
    if lowered in _COMMON or any(item and item.lower() in lowered for item in banned):
        errors.append("Password is too common or contains profile data.")
    return not errors, errors
