"""Liveness vs readiness — le ready ping réellement PostgreSQL."""

from __future__ import annotations

import logging
from typing import Any, Tuple

logger = logging.getLogger(__name__)


def liveness() -> dict[str, str]:
    return {"status": "ok"}


def readiness() -> Tuple[dict[str, Any], int]:
    from app.database import ping_db

    try:
        ping_db()
        return {"status": "ready", "auth": "jwt", "postgresql": True}, 200
    except Exception as exc:
        logger.warning("Readiness PostgreSQL échouée: %s", exc)
        return {"status": "not_ready", "auth": "jwt", "postgresql": False}, 503
