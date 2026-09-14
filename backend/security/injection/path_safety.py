"""WebSecKit — path traversal protection."""

from __future__ import annotations

import os


def assert_safe_relative_path(path: str) -> str:
    trimmed = path.strip()
    if not trimmed or "\x00" in trimmed:
        raise ValueError("Invalid path.")
    if os.path.isabs(trimmed):
        raise ValueError("Absolute path rejected.")
    normalized = os.path.normpath(trimmed)
    if normalized.startswith("..") or os.pardir in normalized.split(os.sep):
        raise ValueError("Path traversal rejected.")
    return normalized
