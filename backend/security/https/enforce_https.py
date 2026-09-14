"""WebSecKit — HTTPS enforcement."""

from __future__ import annotations

import os


def is_https_request(scheme: str, forwarded_proto: str | None, trust_proxy: bool) -> bool:
    if trust_proxy and forwarded_proto:
        proto = forwarded_proto.split(",")[0].strip().lower()
        if proto in {"http", "https"}:
            return proto == "https"
    return scheme == "https"


def should_enforce_https() -> bool:
    return os.getenv("ENV", os.getenv("NODE_ENV", "development")) == "production"


def https_redirect_url(host: str, path: str) -> str:
    if not path.startswith("/"):
        path = "/" + path
    return f"https://{host}{path}"
