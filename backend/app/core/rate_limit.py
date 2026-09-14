"""Limites en mémoire process — première ligne, pas un compteur partagé multi-instance."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock
from typing import Deque, Dict

from fastapi import HTTPException, Request, status

from app.auth import get_client_ip


class SlidingWindowLimiter:
    def __init__(self) -> None:
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key: str, limit: int, window_seconds: float) -> bool:
        now = time.monotonic()
        with self._lock:
            queue = self._hits[key]
            while queue and now - queue[0] > window_seconds:
                queue.popleft()
            if len(queue) >= limit:
                return False
            queue.append(now)
            return True


_limiter = SlidingWindowLimiter()


def enforce(key: str, limit: int, window_seconds: float, *, detail: str) -> None:
    if limit <= 0:
        return
    if not _limiter.allow(key, limit, window_seconds):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
        )


def enforce_login(request: Request, email: str) -> None:
    from app.config import RATE_LIMIT_LOGIN_EMAIL, RATE_LIMIT_LOGIN_IP, RATE_LIMIT_LOGIN_WINDOW

    ip = get_client_ip(request) or "unknown"
    enforce(
        f"login:ip:{ip}",
        RATE_LIMIT_LOGIN_IP,
        RATE_LIMIT_LOGIN_WINDOW,
        detail="Trop de tentatives de connexion. Réessayez plus tard.",
    )
    if email:
        enforce(
            f"login:email:{email.lower()}",
            RATE_LIMIT_LOGIN_EMAIL,
            RATE_LIMIT_LOGIN_WINDOW,
            detail="Trop de tentatives de connexion. Réessayez plus tard.",
        )


def enforce_analyse(request: Request, user) -> None:
    from app.config import (
        RATE_LIMIT_ANALYSE_IP,
        RATE_LIMIT_ANALYSE_ORG,
        RATE_LIMIT_ANALYSE_USER,
        RATE_LIMIT_ANALYSE_WINDOW,
    )

    ip = get_client_ip(request) or "unknown"
    enforce(
        f"analyse:ip:{ip}",
        RATE_LIMIT_ANALYSE_IP,
        RATE_LIMIT_ANALYSE_WINDOW,
        detail="Trop d'analyses depuis cette adresse. Réessayez plus tard.",
    )
    enforce(
        f"analyse:user:{user.id}",
        RATE_LIMIT_ANALYSE_USER,
        RATE_LIMIT_ANALYSE_WINDOW,
        detail="Trop d'analyses pour ce compte. Réessayez plus tard.",
    )
    if getattr(user, "organization_id", None):
        enforce(
            f"analyse:org:{user.organization_id}",
            RATE_LIMIT_ANALYSE_ORG,
            RATE_LIMIT_ANALYSE_WINDOW,
            detail="Trop d'analyses pour cette organisation. Réessayez plus tard.",
        )
