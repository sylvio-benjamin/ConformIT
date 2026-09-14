"""WebSecKit — payment webhook verification wrapper."""

from __future__ import annotations

from ..api.webhooks import verify_webhook_signature


def verify_payment_webhook(raw_body: bytes, signature_header: str | None, timestamp_header: str | None = None) -> bool:
    return verify_webhook_signature(raw_body, signature_header, timestamp_header=timestamp_header)
