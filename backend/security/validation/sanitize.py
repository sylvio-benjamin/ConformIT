"""WebSecKit — HTML escaping and string hygiene."""

from __future__ import annotations

import html


def escape_html(value: str) -> str:
    return html.escape(value, quote=True)


def strip_null_bytes(value: str) -> str:
    return value.replace("\x00", "")


def normalize_email(value: str) -> str:
    return strip_null_bytes(value).strip().lower()
