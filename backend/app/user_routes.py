"""
Routes complémentaires liées à la gestion du compte utilisateur (PostgreSQL).

- Export des données personnelles
- Gestion des sessions actives (révocation)
- Lecture des préférences stockées dans PostgreSQL
"""

from datetime import datetime, timezone
import io
import json
import zipfile

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.organizations import User
from app.models.analyses import Analysis
from app.models.quotas import Quota
from app.models.api_keys import APIKey
from app.models.auth_session import AuthSession
from app.core.permissions import get_current_user


router = APIRouter(prefix="/users", tags=["users"])


def _assert_self_or_admin(current: User, user_id: str) -> None:
    if current.is_platform_admin:
        return
    if str(current.id) != user_id:
        raise HTTPException(status_code=403, detail="Accès refusé")


@router.get("/{user_id}/sessions")
async def get_user_sessions(
    user_id: str,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    _assert_self_or_admin(current, user_id)
    rows = (
        db.query(AuthSession)
        .filter(AuthSession.user_id == current.id)
        .order_by(AuthSession.created_at.desc())
        .limit(20)
        .all()
    )
    return {
        "last_sign_in": current.last_login_at.isoformat() if current.last_login_at else None,
        "created_at": current.created_at.isoformat() if current.created_at else None,
        "sessions": [
            {
                "id": str(s.id),
                "device": s.user_agent or "Session",
                "last_activity": s.created_at.isoformat() if s.created_at else None,
                "revoked": s.revoked_at is not None,
            }
            for s in rows
        ],
    }


@router.post("/{user_id}/logout")
async def revoke_user_sessions(
    user_id: str,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    _assert_self_or_admin(current, user_id)
    now = datetime.now(tz=timezone.utc)
    db.query(AuthSession).filter(
        AuthSession.user_id == current.id,
        AuthSession.revoked_at.is_(None),
    ).update({"revoked_at": now})
    db.commit()
    return {"revoked": True, "revoked_at": now.isoformat()}


@router.post("/{user_id}/export")
async def export_user_data(
    user_id: str,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """
    Compile les données personnelles de l'utilisateur (profil, quotas,
    analyses, préférences) dans une archive ZIP à télécharger depuis PostgreSQL.
    """
    _assert_self_or_admin(current, user_id)
    user = current if str(current.id) == user_id else db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    
    # Récupérer les données depuis PostgreSQL
    profile = {
        "id": str(user.id),
        "email": user.email,
        "nom": user.nom,
        "prenom": user.prenom,
        "entreprise": user.entreprise,
        "telephone": user.telephone,
        "abonnement": user.abonnement,
        "preferences": user.preferences,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }
    
    # Récupérer les quotas
    quotas = db.query(Quota).filter(Quota.user_id == user.id).all()
    quota_data = {
        str(q.month): {
            "count": q.count,
            "last_updated": q.last_updated.isoformat() if q.last_updated else None,
        }
        for q in quotas
    }
    
    # Récupérer les analyses
    analyses = db.query(Analysis).filter(Analysis.employee_id == user.id).all()
    analyses_data = {
        a.slug: {
            "slug": a.slug,
            "nom": a.company_name,
            "type": a.document_type,
            "rcs": a.rcs,
            "score_total": a.total_score,
            "risque": a.risk_level,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in analyses
    }
    
    # Récupérer les clés API
    api_keys = db.query(APIKey).filter(APIKey.user_id == user.id).all()
    api_key_data = {
        str(ak.id): {
            "name": ak.name,
            "is_active": ak.is_active,
            "created_at": ak.created_at.isoformat() if ak.created_at else None,
            "last_used_at": ak.last_used_at.isoformat() if ak.last_used_at else None,
        }
        for ak in api_keys
    }
    
    export_payload = {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "profile": profile,
        "quota": quota_data,
        "analyses": analyses_data,
        "api_keys": api_key_data,
    }

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "user_data.json",
            json.dumps(export_payload, indent=2, ensure_ascii=False),
        )

    buffer.seek(0)
    filename = f"export_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"'
    }

    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers=headers,
    )


@router.put("/{user_id}/preferences")
async def update_preferences(
    user_id: str,
    payload: dict,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """
    Met à jour partiellement les préférences utilisateur stockées dans PostgreSQL.
    """
    _assert_self_or_admin(current, user_id)
    user = current if str(current.id) == user_id else db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    
    try:
        # Mettre à jour les préférences
        if user.preferences is None:
            user.preferences = {}
        
        # Fusionner les nouvelles préférences avec les existantes
        user.preferences.update(payload)
        db.commit()
        db.refresh(user)
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur PostgreSQL: {exc}") from exc

    return JSONResponse({"updated": True, "preferences": user.preferences})
