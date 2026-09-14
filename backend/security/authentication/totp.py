"""WebSecKit — TOTP (RFC 6238)."""

from __future__ import annotations

import hmac
import hashlib
import os
import struct
import time

PERIOD = 30
DIGITS = 6


def generate_totp_secret() -> bytes:
    return os.urandom(20)


def verify_totp(secret: bytes, code: str, now: float | None = None, window: int = 1) -> bool:
    trimmed = code.replace(" ", "")
    if not trimmed.isdigit() or len(trimmed) != 6:
        return False
    counter = int((now if now is not None else time.time()) / PERIOD)
    for offset in range(-window, window + 1):
        if hmac.compare_digest(_generate_code(secret, counter + offset), trimmed):
            return True
    return False


def _generate_code(secret: bytes, counter: int) -> str:
    msg = struct.pack(">Q", counter)
    digest = hmac.new(secret, msg, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    binary = ((digest[offset] & 0x7F) << 24) | (digest[offset + 1] << 16) | (digest[offset + 2] << 8) | digest[offset + 3]
    return str(binary % (10**DIGITS)).zfill(DIGITS)
