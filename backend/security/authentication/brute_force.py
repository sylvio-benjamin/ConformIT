"""WebSecKit — login brute-force protection."""

from __future__ import annotations

from ..config.security_config import LOCKOUT_MS, MAX_LOGIN_ATTEMPTS
from ..rate_limit.rate_limiter import consume, reset


def login_attempt_key(ip: str, identifier: str) -> str:
    return f"login:{ip}:{identifier.lower()}"


def check_login_allowed(ip: str, identifier: str) -> dict[str, int | bool]:
    result = consume(login_attempt_key(ip, identifier), MAX_LOGIN_ATTEMPTS, LOCKOUT_MS)
    return {
        "blocked": not result["allowed"],
        "remaining_attempts": result["remaining"],
        "retry_after": result["retry_after"],
    }


def record_login_success(ip: str, identifier: str) -> None:
    reset(login_attempt_key(ip, identifier))
