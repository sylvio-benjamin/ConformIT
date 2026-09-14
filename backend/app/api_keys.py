"""Routes pour la gestion des clés API dédiées aux plans Enterprise (PostgreSQL)."""

import hashlib
import secrets
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.organizations import User
from app.models.api_keys import APIKey
from app.services.plan_service import PlanService
from app.core.permissions import get_current_user


router = APIRouter(prefix="/api-keys", tags=["api_keys"])


def _ensure_enterprise_plan(user_id: str):
    plan = PlanService.get_user_plan(user_id)
    if plan != "enterprise":
        raise HTTPException(status_code=403, detail="Les clés API sont réservées au plan Enterprise.")


@router.get("/{user_id}")
async def get_api_key_status(
    user_id: str,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """Retourne l'état de la clé API pour l'utilisateur."""
    if not current.is_platform_admin and str(current.id) != user_id:
        raise HTTPException(status_code=403, detail="Accès refusé")
    _ensure_enterprise_plan(str(current.id))
    user = current
    
    # Récupérer la clé API active de l'utilisateur
    api_key = db.query(APIKey).filter(
        APIKey.user_id == user.id,
        APIKey.is_active.is_(True)
    ).first()
    
    if not api_key:
        return {"has_key": False}
    
    return {
        "has_key": True,
        "created_at": api_key.created_at.isoformat() if api_key.created_at else None,
        "last_used_at": api_key.last_used_at.isoformat() if api_key.last_used_at else None,
        "name": api_key.name
    }


@router.post("/generate/")
async def generate_api_key(
    request: Request,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """Génère une nouvelle clé API pour un utilisateur Enterprise."""
    body = await request.json()
    _ensure_enterprise_plan(str(current.id))
    user = current
    
    # Désactiver l'ancienne clé si nécessaire
    previous_key = db.query(APIKey).filter(
        APIKey.user_id == user.id,
        APIKey.is_active.is_(True)
    ).first()
    
    if previous_key:
        previous_key.is_active = False
        db.commit()
    
    # Générer une nouvelle clé
    token = secrets.token_urlsafe(32)
    hashed = hashlib.sha256(token.encode()).hexdigest()
    
    api_key = APIKey(
        user_id=user.id,
        key_hash=hashed,
        name=body.get("name"),  # Nom optionnel
        is_active=True
    )
    
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    
    return {
        "api_key": token,
        "created_at": api_key.created_at.isoformat() if api_key.created_at else None
    }


@router.delete("/{user_id}")
async def revoke_api_key(
    user_id: str,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """Révoque la clé API actuelle."""
    if not current.is_platform_admin and str(current.id) != user_id:
        raise HTTPException(status_code=403, detail="Accès refusé")
    _ensure_enterprise_plan(str(current.id))
    user = current
    
    # Désactiver toutes les clés actives de l'utilisateur
    api_keys = db.query(APIKey).filter(
        APIKey.user_id == user.id,
        APIKey.is_active.is_(True)
    ).all()
    
    if not api_keys:
        return {"revoked": False}
    
    for api_key in api_keys:
        api_key.is_active = False
    
    db.commit()
    
    return {"revoked": True, "count": len(api_keys)}
