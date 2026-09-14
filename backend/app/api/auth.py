"""Authentification FastAPI : inscription, login, refresh, logout, mot de passe."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.config import BOOTSTRAP_ADMIN_EMAIL, ENV
from app.core.permissions import get_current_user
from app.core.security import (
    REFRESH_COOKIE,
    clear_auth_cookies,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    new_reset_token,
    set_auth_cookies,
    verify_password,
)
from app.database import get_db
from app.models.auth_session import AuthSession, PasswordResetToken
from app.models.organizations import Organization, User

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class RegisterBody(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    nom: str = Field(min_length=1, max_length=100)
    entreprise: Optional[str] = Field(default=None, max_length=255)


class LoginBody(BaseModel):
    email: EmailStr
    password: str


class ForgotBody(BaseModel):
    email: EmailStr


class ResetBody(BaseModel):
    token: str
    password: str = Field(min_length=8)


class ChangePasswordBody(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


def _user_payload(user: User) -> dict:
    return {
        "id": str(user.id),
        "uid": str(user.id),
        "email": user.email,
        "nom": user.nom,
        "prenom": user.prenom,
        "entreprise": user.entreprise,
        "telephone": user.telephone,
        "abonnement": user.abonnement or "basic",
        "admin": bool(user.is_platform_admin),
        "is_platform_admin": bool(user.is_platform_admin),
        "organization_id": str(user.organization_id) if user.organization_id else None,
        "preferences": user.preferences or {},
        "must_set_password": user.password_hash is None,
    }


def _issue_session(db: Session, user: User, request: Request, response: Response) -> dict:
    access, jti, expires = create_access_token(
        user.id, user.organization_id, bool(user.is_platform_admin)
    )
    refresh, _, _ = create_refresh_token(user.id)
    session = AuthSession(
        user_id=user.id,
        jti=jti,
        expires_at=expires,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    db.add(session)
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    set_auth_cookies(response, access, refresh)
    return {"user": _user_payload(user)}


@router.post("/register", status_code=201)
async def register(body: RegisterBody, request: Request, response: Response, db: Session = Depends(get_db)):
    from app.core.rate_limit import enforce_login

    email = body.email.lower().strip()
    enforce_login(request, email)
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Cet email est déjà utilisé")

    org = Organization(
        name=body.entreprise or f"Organisation de {body.nom}",
        plan="basic",
        subscription_status="active",
    )
    db.add(org)
    db.flush()

    is_admin = bool(BOOTSTRAP_ADMIN_EMAIL) and email == BOOTSTRAP_ADMIN_EMAIL
    user = User(
        email=email,
        password_hash=hash_password(body.password),
        nom=body.nom.strip(),
        entreprise=body.entreprise,
        organization_id=org.id,
        abonnement="basic",
        is_platform_admin=is_admin,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _issue_session(db, user, request, response)


@router.post("/login")
async def login(body: LoginBody, request: Request, response: Response, db: Session = Depends(get_db)):
    from app.core.rate_limit import enforce_login

    email = body.email.lower().strip()
    enforce_login(request, email)
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    if not user.password_hash:
        raise HTTPException(
            status_code=403,
            detail="Compte migré sans mot de passe. Utilisez « mot de passe oublié ».",
        )
    if not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    return _issue_session(db, user, request, response)


@router.post("/refresh")
async def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    raw = request.cookies.get(REFRESH_COOKIE)
    if not raw:
        raise HTTPException(status_code=401, detail="Refresh manquant")
    try:
        payload = decode_token(raw, expected_type="refresh")
    except Exception:
        raise HTTPException(status_code=401, detail="Refresh invalide")

    user = db.query(User).filter(User.id == payload.get("sub")).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Compte inactif")
    return _issue_session(db, user, request, response)


@router.post("/logout")
async def logout(
    response: Response,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    db.query(AuthSession).filter(
        AuthSession.user_id == user.id,
        AuthSession.revoked_at.is_(None),
    ).update({"revoked_at": now})
    db.commit()
    clear_auth_cookies(response)
    return {"ok": True}


@router.get("/me")
async def me(user: User = Depends(get_current_user)):
    return _user_payload(user)


@router.post("/forgot-password")
async def forgot_password(body: ForgotBody, db: Session = Depends(get_db)):
    """Ne révèle pas si l'email existe. En développement, le jeton est renvoyé pour les tests."""
    email = body.email.lower().strip()
    user = db.query(User).filter(User.email == email).first()
    payload = {"ok": True}
    if user:
        raw = new_reset_token()
        db.add(
            PasswordResetToken(
                user_id=user.id,
                token_hash=hash_token(raw),
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            )
        )
        db.commit()
        if ENV != "production":
            payload["reset_token"] = raw
            payload["dev_hint"] = "Jeton exposé uniquement hors production"
    return payload


@router.post("/reset-password")
async def reset_password(body: ResetBody, db: Session = Depends(get_db)):
    token_row = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.token_hash == hash_token(body.token),
            PasswordResetToken.used_at.is_(None),
        )
        .first()
    )
    if not token_row or token_row.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Jeton invalide ou expiré")
    user = db.query(User).filter(User.id == token_row.user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="Utilisateur introuvable")
    user.password_hash = hash_password(body.password)
    token_row.used_at = datetime.now(timezone.utc)
    db.query(AuthSession).filter(
        AuthSession.user_id == user.id,
        AuthSession.revoked_at.is_(None),
    ).update({"revoked_at": datetime.now(timezone.utc)})
    db.commit()
    return {"ok": True}


@router.post("/change-password")
async def change_password(
    body: ChangePasswordBody,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user.password_hash or not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Mot de passe actuel incorrect")
    user.password_hash = hash_password(body.new_password)
    db.commit()
    return {"ok": True}
