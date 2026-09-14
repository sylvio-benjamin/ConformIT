"""
Routes API pour la gestion des plans et quotas.
"""

from fastapi import APIRouter, Request, HTTPException, Header, Depends
from fastapi.responses import JSONResponse
from typing import Optional
from app.services.plan_service import PlanService, _find_user
from app.core.permissions import get_current_user
from app.models.organizations import User

router = APIRouter()


@router.get("/quota/me")
async def get_my_quota(user: User = Depends(get_current_user)):
    try:
        quota = PlanService.get_user_quota(str(user.id))
        return JSONResponse(quota)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération du quota: {str(e)}")


@router.get("/quota/{user_id}")
async def get_user_quota(user_id: str, user: User = Depends(get_current_user)):
    if not user.is_platform_admin and str(user.id) != user_id:
        raise HTTPException(status_code=403, detail="Accès refusé")
    """
    Récupère le quota actuel d'un utilisateur.
    
    Returns:
        - count: Nombre d'analyses effectuées ce mois
        - limit: Limite du plan (None si illimité)
        - plan: Plan de l'utilisateur
        - month: Mois courant
        - reset_date: Date de réinitialisation
        - unlimited: True si le plan est illimité
    """
    try:
        quota = PlanService.get_user_quota(user_id)
        return JSONResponse(quota)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération du quota: {str(e)}")


@router.get("/plan/{user_id}")
async def get_user_plan(user_id: str, user: User = Depends(get_current_user)):
    if not user.is_platform_admin and str(user.id) != user_id:
        raise HTTPException(status_code=403, detail="Accès refusé")
    """
    Récupère le plan d'un utilisateur.
    
    Returns:
        - plan: Plan de l'utilisateur
        - limit: Limite d'analyses
        - features: Fonctionnalités disponibles
    """
    try:
        from app.services.plan_service import PLAN_LIMITS, PLAN_FEATURES
        
        plan = PlanService.get_user_plan(user_id)
        limit = PlanService.get_plan_limit(plan)
        features = PLAN_FEATURES.get(plan, PLAN_FEATURES["basic"])
        
        return JSONResponse({
            "plan": plan,
            "limit": limit if limit != float("inf") else None,
            "unlimited": limit == float("inf"),
            "features": features,
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération du plan: {str(e)}")


@router.get("/history/{user_id}")
async def get_user_history(user_id: str, limit: int = 50, user: User = Depends(get_current_user)):
    if not user.is_platform_admin and str(user.id) != user_id:
        raise HTTPException(status_code=403, detail="Accès refusé")
    """
    Récupère l'historique des analyses d'un utilisateur depuis PostgreSQL.
    
    Args:
        user_id: Identifiant utilisateur (UUID)
        limit: Nombre maximum d'analyses à retourner (default: 50)
        
    Returns:
        Liste des analyses de l'utilisateur
    """
    try:
        from app.database import SessionLocal
        from app.models.organizations import User
        from app.models.analyses import Analysis
        
        db = SessionLocal()
        try:
            user = _find_user(db, user_id)
            if not user:
                return JSONResponse({"analyses": [], "total": 0})
            
            # Récupérer les analyses depuis PostgreSQL
            analyses = db.query(Analysis).filter(
                Analysis.employee_id == user.id
            ).order_by(Analysis.created_at.desc()).limit(limit).all()
            
            # Convertir en format JSON
            analyses_list = []
            for analysis in analyses:
                analyses_list.append({
                    "slug": analysis.slug,
                    "nom": analysis.company_name,
                    "nom_entreprise": analysis.company_name,
                    "date": analysis.created_at.isoformat() if analysis.created_at else None,
                    "score_total": analysis.total_score,
                    "score": analysis.total_score,
                    "risque": analysis.risk_level,
                    "niveau_risque": analysis.risk_level,
                    "type": analysis.document_type,
                    "rcs": analysis.rcs,
                    "nom_fichier": analysis.filename,
                })
            
            return JSONResponse({"analyses": analyses_list, "total": len(analyses_list)})
        finally:
            db.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération de l'historique: {str(e)}")

