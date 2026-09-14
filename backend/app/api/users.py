"""
API REST pour la gestion des utilisateurs (PostgreSQL, auth JWT).
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID as PyUUID

from app.database import get_db
from app.models.organizations import User
from app.models.collaborators import Collaborator
from app.core.permissions import get_current_user

router = APIRouter(prefix="/api/users", tags=["users"])


class ProfileUpdate(BaseModel):
    nom: Optional[str] = None
    prenom: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    entreprise: Optional[str] = None
    telephone: Optional[str] = None
    preferences: Optional[dict] = None


class CollaboratorCreate(BaseModel):
    email: EmailStr


@router.get("/me")
async def read_me(user: User = Depends(get_current_user)):
    """Profil de l'utilisateur authentifié."""
    return {
        "id": str(user.id),
        "uid": str(user.id),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "nom": user.nom,
        "prenom": user.prenom,
        "entreprise": user.entreprise,
        "telephone": user.telephone,
        "abonnement": user.abonnement,
        "admin": bool(user.is_platform_admin),
        "preferences": user.preferences or {},
        "organization_id": str(user.organization_id) if user.organization_id else None,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
    }


@router.put("/me")
async def update_user_profile(
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Met à jour le profil de l'utilisateur authentifié."""
    if payload.first_name is not None:
        user.first_name = payload.first_name
    if payload.last_name is not None:
        user.last_name = payload.last_name
    if payload.nom is not None:
        user.nom = payload.nom
    if payload.prenom is not None:
        user.prenom = payload.prenom
    if payload.entreprise is not None:
        user.entreprise = payload.entreprise
    if payload.telephone is not None:
        user.telephone = payload.telephone
    if payload.preferences is not None:
        user.preferences = payload.preferences
    
    db.commit()
    db.refresh(user)
    
    return {
        "id": str(user.id),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "nom": user.nom,
        "prenom": user.prenom,
        "entreprise": user.entreprise,
        "telephone": user.telephone,
        "preferences": user.preferences or {},
        "abonnement": user.abonnement,
    }


@router.post("/me/cancel-subscription")
async def cancel_subscription(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    user.abonnement = "basic"
    db.commit()
    return {"abonnement": "basic", "subscription_status": "cancelled"}


@router.get("/{user_id}/collaborators")
async def get_collaborators(
    user_id: str,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """Récupère les collaborateurs d'un utilisateur."""
    if not current.is_platform_admin and str(current.id) != user_id:
        raise HTTPException(status_code=403, detail="Accès refusé")
    user = current if str(current.id) == user_id else db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    collaborators = db.query(Collaborator).filter(Collaborator.user_id == user.id).all()
    
    return {
        "collaborators": [
            {
                "id": str(c.id),
                "email": c.email,
                "added_at": c.added_at.isoformat() if c.added_at else None,
            }
            for c in collaborators
        ]
    }


@router.post("/{user_id}/collaborators")
async def add_collaborator(
    user_id: str,
    payload: CollaboratorCreate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """Ajoute un collaborateur."""
    if not current.is_platform_admin and str(current.id) != user_id:
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    user = current if str(current.id) == user_id else db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    # Vérifier la limite (2 collaborateurs max)
    existing_count = db.query(Collaborator).filter(Collaborator.user_id == user.id).count()
    if existing_count >= 2:
        raise HTTPException(status_code=400, detail="Limite de collaborateurs atteinte (2 max)")
    
    # Vérifier si déjà existant
    existing = db.query(Collaborator).filter(
        Collaborator.user_id == user.id,
        Collaborator.email == payload.email.lower()
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Ce collaborateur est déjà ajouté")
    
    collaborator = Collaborator(
        user_id=user.id,
        email=payload.email.lower()
    )
    db.add(collaborator)
    db.commit()
    db.refresh(collaborator)
    
    return {
        "id": str(collaborator.id),
        "email": collaborator.email,
        "added_at": collaborator.added_at.isoformat() if collaborator.added_at else None,
    }


@router.delete("/{user_id}/collaborators/{collaborator_id}")
async def remove_collaborator(
    user_id: str,
    collaborator_id: str,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """Supprime un collaborateur."""
    if not current.is_platform_admin and str(current.id) != user_id:
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    user = current if str(current.id) == user_id else db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    collaborator = db.query(Collaborator).filter(
        Collaborator.id == PyUUID(collaborator_id),
        Collaborator.user_id == user.id
    ).first()
    
    if not collaborator:
        raise HTTPException(status_code=404, detail="Collaborateur non trouvé")
    
    db.delete(collaborator)
    db.commit()
    
    return {"success": True}

