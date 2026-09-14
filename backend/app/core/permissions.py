"""Dépendances FastAPI : utilisateur courant, admin, isolation organisation.

Pont WebSecKit : assert_ownership / require_permission sans remplacer JWT.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import ACCESS_COOKIE, decode_token
from app.database import get_db
from app.models.auth_session import AuthSession
from app.models.organizations import User
from security.authorization.ownership import assert_ownership
from security.authorization.rbac import AuthorizationError, require_permission


def roles_for_user(user: User) -> list[str]:
    if user.is_platform_admin:
        return ["admin"]
    return ["user"]


def enforce_permission(user: User, permission: str) -> None:
    try:
        require_permission(roles_for_user(user), permission)
    except AuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


def _extract_bearer(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    if not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ", 1)[1].strip()
    return token or None


def get_current_user(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
    da_access: Optional[str] = Cookie(None, alias=ACCESS_COOKIE),
) -> User:
    token = _extract_bearer(authorization) or da_access
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentification requise",
        )

    try:
        payload = decode_token(token, expected_type="access")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session invalide ou expirée",
        )

    jti = payload.get("jti")
    user_id = payload.get("sub")
    if not jti or not user_id:
        raise HTTPException(status_code=401, detail="Jeton incomplet")

    session = (
        db.query(AuthSession)
        .filter(AuthSession.jti == jti, AuthSession.revoked_at.is_(None))
        .first()
    )
    if not session:
        raise HTTPException(status_code=401, detail="Session révoquée")

    user = db.query(User).filter(User.id == UUID(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Compte inactif ou introuvable")

    return user


def require_authenticated_user(user: User = Depends(get_current_user)) -> User:
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    enforce_permission(user, "admin:access")
    if not user.is_platform_admin:
        raise HTTPException(status_code=403, detail="Droits administrateur requis")
    return user


def require_upload_permission(user: User = Depends(get_current_user)) -> User:
    enforce_permission(user, "files:upload")
    return user


def require_organization_access(
    organization_id: UUID,
    user: User = Depends(get_current_user),
) -> User:
    assert_same_organization(user, organization_id)
    return user


def assert_same_organization(user: User, organization_id: Optional[UUID]) -> None:
    """Isolation multi-tenant + pont WebSecKit ownership (IDOR)."""
    if user.is_platform_admin:
        assert_ownership(str(user.id), str(user.id), admin=True)
        return
    if organization_id is None or user.organization_id != organization_id:
        raise HTTPException(status_code=403, detail="Ressource hors de votre organisation")
    assert_ownership(
        str(user.organization_id),
        str(organization_id),
        admin=False,
    )
