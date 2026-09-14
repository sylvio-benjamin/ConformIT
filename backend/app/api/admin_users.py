"""Administration des utilisateurs (plateforme)."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.core.permissions import require_admin
from app.core.security import hash_password
from app.database import get_db
from app.models.organizations import Organization, User

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


class AdminCreateUser(BaseModel):
    email: EmailStr
    nom: str = Field(min_length=1)
    prenom: str = ""
    entreprise: str = ""
    admin: bool = False
    password: str = Field(default="ChangeMe123!")


@router.get("/users")
async def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    users = db.query(User).order_by(User.created_at.desc()).all()
    return {
        "users": [
            {
                "id": str(u.id),
                "email": u.email,
                "nom": u.nom,
                "prenom": u.prenom,
                "entreprise": u.entreprise,
                "abonnement": u.abonnement,
                "admin": bool(u.is_platform_admin),
                "is_active": u.is_active,
                "organization_id": str(u.organization_id) if u.organization_id else None,
            }
            for u in users
        ]
    }


@router.post("/users", status_code=201)
async def create_user(
    payload: AdminCreateUser,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    email = payload.email.lower().strip()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="Cet email est déjà utilisé")
    org = Organization(name=payload.entreprise or f"Organisation de {payload.nom}", plan="basic")
    db.add(org)
    db.flush()
    user = User(
        email=email,
        password_hash=hash_password(payload.password),
        nom=payload.nom,
        prenom=payload.prenom,
        entreprise=payload.entreprise,
        organization_id=org.id,
        is_platform_admin=payload.admin,
        abonnement="basic",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": str(user.id), "email": user.email}
