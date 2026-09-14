"""WebSecKit — in-memory rate limiter."""

from __future__ import annotations

import time

from ..config.security_config import RATE_LIMITS

_counters: dict[str, tuple[int, float]] = {}


def consume(key: str, max_hits: int, window_ms: int) -> dict[str, int | bool]:
    now = time.time() * 1000
    count, reset_at = _counters.get(key, (0, 0.0))
    if reset_at <= now:
        _counters[key] = (1, now + window_ms)
        return {"allowed": True, "remaining": max_hits - 1, "retry_after": 0, "limit": max_hits}
    if count >= max_hits:
        return {
            "allowed": False,
            "remaining": 0,
            "retry_after": max(1, int((reset_at - now) / 1000)),
            "limit": max_hits,
        }
    _counters[key] = (count + 1, reset_at)
    return {"allowed": True, "remaining": max(0, max_hits - count - 1), "retry_after": 0, "limit": max_hits}


def rate_limit(bucket: str, ip: str = "anon", user_id: str = "-", route: str = "*") -> dict[str, int | bool]:
    spec = RATE_LIMITS[bucket]
    key = f"{bucket}:{ip}:{user_id}:{route}"
    return consume(key, spec["max"], spec["window_ms"])


def reset(key: str) -> None:
    _counters.pop(key, None)


def client_ip(headers: dict[str, str], trust_proxy: bool) -> str:
    if trust_proxy:
        forwarded = headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return headers.get("x-real-ip", "unknown")
