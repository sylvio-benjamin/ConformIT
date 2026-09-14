"""WebSecKit — RBAC deny-by-default (matrice ConformIT)."""

from __future__ import annotations

from typing import Iterable

ROLES = ("admin", "user", "guest")
PERMISSIONS = {
    "admin": {
        "users:read",
        "users:write",
        "admin:access",
        "analyses:read",
        "analyses:write",
        "files:upload",
    },
    "user": {
        "users:read",
        "analyses:read",
        "analyses:write",
        "files:upload",
    },
    "guest": set(),
}


class AuthorizationError(Exception):
    status = 403


def has_permission(roles: Iterable[str], permission: str) -> bool:
    return any(permission in PERMISSIONS.get(role, set()) for role in roles)


def require_permission(roles: Iterable[str] | None, permission: str) -> None:
    if not roles or not has_permission(roles, permission):
        raise AuthorizationError("Insufficient permission.")
