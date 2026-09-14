"""WebSecKit — parameterized-query policy helpers."""

from __future__ import annotations

import re

_CONCAT_SQL = re.compile(r"\b(select|insert|update|delete|drop|union)\b.*(\+|f['\"]|%)", re.I)


def looks_like_concatenated_sql(source: str) -> bool:
    return bool(_CONCAT_SQL.search(source))


def reject_unsafe_identifier(identifier: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", identifier):
        raise ValueError("Unsafe identifier.")
    return identifier
