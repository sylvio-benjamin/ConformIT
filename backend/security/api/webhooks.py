"""WebSecKit — HMAC webhook verification (raw body)."""

from __future__ import annotations

import hashlib
import hmac
import os
import time

from ..config.security_config import WEBHOOK_SKEW_MS


def verify_webhook_signature(
    raw_body: bytes,
    signature_header: str | None,
    secret: str | None = None,
    timestamp_header: str | None = None,
    now_ms: float | None = None,
) -> bool:
    secret = secret or os.getenv("WEBHOOK_HMAC_SECRET")
    if not secret or not signature_header:
        return False
    now = time.time() * 1000 if now_ms is None else now_ms
    if timestamp_header:
        ts = float(timestamp_header)
        if len(timestamp_header) == 10:
            ts *= 1000
        if abs(now - ts) > WEBHOOK_SKEW_MS:
            return False
    expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    provided = signature_header.removeprefix("sha256=")
    return hmac.compare_digest(expected, provided)
