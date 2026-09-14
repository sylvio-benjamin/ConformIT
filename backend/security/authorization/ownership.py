"""WebSecKit — resource ownership (IDOR/BOLA)."""

from __future__ import annotations

from .rbac import AuthorizationError


def assert_ownership(principal_id: str | None, owner_id: str, admin: bool = False) -> None:
    if principal_id is None:
        raise AuthorizationError("Authentication required.")
    if admin:
        return
    if principal_id != owner_id:
        raise AuthorizationError("You cannot access this resource.")
