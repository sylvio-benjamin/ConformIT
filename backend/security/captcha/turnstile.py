"""WebSecKit — Cloudflare Turnstile verification."""

from __future__ import annotations

import json
import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def verify_turnstile_token(token: str | None, ip: str | None = None, secret: str | None = None) -> bool:
    secret = secret or os.getenv("TURNSTILE_SECRET_KEY")
    if not secret or not token:
        return False
    payload = {"secret": secret, "response": token}
    if ip and ip != "unknown":
        payload["remoteip"] = ip
    request = Request(
        "https://challenges.cloudflare.com/turnstile/v0/siteverify",
        data=urlencode(payload).encode(),
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urlopen(request, timeout=5) as response:  # noqa: S310 - fixed vendor URL
        body = json.loads(response.read().decode())
    return bool(body.get("success"))
