"""WebSecKit — security logger with redaction."""

from __future__ import annotations

import json
from datetime import datetime, timezone

REDACT_KEYS = {
    "password",
    "pass",
    "token",
    "accesstoken",
    "refreshtoken",
    "authorization",
    "cookie",
    "secret",
    "secretkey",
    "apikey",
    "creditcard",
    "cardnumber",
    "cvv",
}


def redact(value: object) -> object:
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, dict):
        return {
            key: "[redacted]" if key.lower() in REDACT_KEYS else redact(nested)
            for key, nested in value.items()
        }
    return value


def security_log(event: str, data: dict[str, object] | None = None, level: str = "info") -> dict[str, object]:
    entry = {
        "at": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "level": level,
        "data": redact(data or {}),
    }
    print(json.dumps(entry))
    return entry
