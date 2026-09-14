"""
API REST pour la gestion des analyses, entreprises et documents (PostgreSQL).
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Any, Optional

from app.database import get_db
from app.models.analyses import Analysis, Company, Document, Counter
from app.models.organizations import User, Organization
from app.core.permissions import get_current_user, assert_same_organization

router = APIRouter(prefix="/api/analyses", tags=["analyses"])


class AnalysisUpdate(BaseModel):
    company_name: Optional[str] = None
    document_type: Optional[str] = None
    rcs: Optional[str] = None
    total_score: Optional[int] = None
    risk_level: Optional[str] = None
    precision: Optional[float] = None
    quality: Optional[str] = None
    details: Optional[Any] = None


def get_next_analysis_id(db: Session, user: User) -> int:
    """Génère le prochain ID d'analyse pour un utilisateur."""
    counter_key = f"analyse_{user.id}"
    counter = db.query(Counter).filter(Counter.key == counter_key).first()
    
    if not counter:
        counter = Counter(key=counter_key, value=0)
        db.add(counter)
    
    counter.value += 1
    db.commit()
    db.refresh(counter)
    return counter.value


@router.get("")
async def list_analyses(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Liste des analyses de l'organisation de l'utilisateur."""
    query = db.query(Analysis)
    if not user.is_platform_admin:
        query = query.filter(Analysis.organization_id == user.organization_id)
    analyses = query.order_by(Analysis.analysis_number.desc()).all()
    
    return {
        "analyses": [
            {
                "id": a.analysis_number,  # Utiliser le numéro d'analyse au lieu de l'UUID
                "analysis_id": str(a.id),  # Garder l'UUID pour référence interne
                "analysis_number": a.analysis_number,  # Numéro d'analyse (1, 2, 3, etc.)
                "slug": a.slug,
                "nom": a.company_name,
                "nom_entreprise": a.company_name,
                "type": a.document_type,
                "type_document": a.document_type,
                "rcs": a.rcs,
                "RCS": a.rcs,
                "score_total": a.total_score,
                "score": a.total_score,
                "risque": a.risk_level,
                "niveau_risque": a.risk_level,
                "precision": float(a.precision) if a.precision else None,
                "qualite": a.quality or (str(a.precision) if a.precision else None),
                "nom_fichier": a.filename,
                "document_type": a.document_type,
                "risk_color": a.risk_color,
                "status": a.status,
                "details": a.details or [],
                "date": a.created_at.isoformat() if a.created_at else None,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in analyses
        ]
    }


@router.get("/{slug}")
async def get_analysis_by_slug(
    slug: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Récupère une analyse par son slug (isolée par organisation)."""
    analysis = db.query(Analysis).filter(Analysis.slug == slug).first()
    if analysis:
        assert_same_organization(user, analysis.organization_id)
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analyse non trouvée")
    
    return {
        "id": analysis.analysis_number,  # Utiliser le numéro d'analyse au lieu de l'UUID
        "analysis_id": str(analysis.id),  # Garder l'UUID pour référence interne
        "analysis_number": analysis.analysis_number,  # Numéro d'analyse (1, 2, 3, etc.)
        "slug": analysis.slug,
        "nom": analysis.company_name,
        "nom_entreprise": analysis.company_name,
        "type": analysis.document_type,
        "type_document": analysis.document_type,
        "rcs": analysis.rcs,
        "RCS": analysis.rcs,
        "score_total": analysis.total_score,
        "score": analysis.total_score,
        "risque": analysis.risk_level,
        "niveau_risque": analysis.risk_level,
        "precision": float(analysis.precision) if analysis.precision else None,
        "qualite": analysis.quality or (str(analysis.precision) if analysis.precision else None),
        "nom_fichier": analysis.filename,
        "document_type": analysis.document_type,
        "risk_color": analysis.risk_color,
        "status": analysis.status,
        "details": analysis.details or [],
        "analyseTerminee": analysis.status == "Terminée",
        "date": analysis.created_at.isoformat() if analysis.created_at else None,
        "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
    }


@router.post("")
async def create_analysis(
    slug: str = Query(..., description="Slug de l'analyse"),
    company_name: str = Query(..., description="Nom de l'entreprise"),
    document_type: Optional[str] = Query(None),
    rcs: Optional[str] = Query(None),
    siret: Optional[str] = Query(None),
    total_score: Optional[int] = Query(None),
    risk_level: Optional[str] = Query(None),
    precision: Optional[float] = Query(None),
    quality: Optional[str] = Query(None),
    filename: Optional[str] = Query(None),
    details: Optional[dict] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Crée une nouvelle analyse pour l'utilisateur authentifié."""
    # Vérifier si l'analyse existe déjà
    existing = db.query(Analysis).filter(Analysis.slug == slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Une analyse avec ce slug existe déjà")
    
    # Récupérer ou créer l'organisation
    if not user.organization_id:
        org = Organization(name=f"Organisation de {user.email}", plan="basic")
        db.add(org)
        db.flush()
        user.organization_id = org.id
        db.commit()
    
    # Générer le numéro d'analyse pour cet utilisateur (1, 2, 3, etc.)
    analysis_number = get_next_analysis_id(db, user)
    
    # Créer l'analyse
    analysis = Analysis(
        slug=slug,
        analysis_number=analysis_number,  # Numéro d'analyse (1, 2, 3, etc.)
        organization_id=user.organization_id,
        employee_id=user.id,
        company_name=company_name,
        document_type=document_type,
        rcs=rcs,
        siret=siret,
        total_score=total_score,
        risk_level=risk_level,
        precision=precision,
        quality=quality,
        filename=filename,
        details=details,
        status="Terminée"
    )
    
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    
    # Intégrer automatiquement dans la GRC si le score indique des risques
    integration_result = None
    if total_score and (total_score > 40 or risk_level in ['High', 'Critical', 'high', 'critical']):
        try:
            from app.services.analysis_grc_integration import AnalysisGRCIntegrationService
            integration_service = AnalysisGRCIntegrationService(db)
            integration_result = integration_service.integrate_analysis_to_grc(
                analysis_id=str(analysis.id),
                user_id=str(user.id),
                force=False
            )
        except Exception as e:
            # Logger l'erreur mais ne pas bloquer la création de l'analyse
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur lors de l'intégration GRC pour l'analyse {analysis.slug}: {e}")
    
    return {
        "id": analysis.analysis_number,  # Utiliser le numéro d'analyse
        "analysis_id": str(analysis.id),  # Garder l'UUID pour référence interne
        "analysis_number": analysis.analysis_number,
        "slug": analysis.slug,
        "message": "Analyse créée avec succès",
        "grc_integration": integration_result
    }


@router.put("/{slug}")
async def update_analysis(
    slug: str,
    payload: AnalysisUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Met à jour une analyse."""
    analysis = db.query(Analysis).filter(Analysis.slug == slug).first()
    if analysis:
        assert_same_organization(user, analysis.organization_id)
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analyse non trouvée")
    
    if payload.company_name is not None:
        analysis.company_name = payload.company_name
    if payload.document_type is not None:
        analysis.document_type = payload.document_type
    if payload.rcs is not None:
        analysis.rcs = payload.rcs
    if payload.total_score is not None:
        analysis.total_score = payload.total_score
    if payload.risk_level is not None:
        analysis.risk_level = payload.risk_level
    if payload.precision is not None:
        analysis.precision = payload.precision
    if payload.quality is not None:
        analysis.quality = payload.quality
    if payload.details is not None:
        analysis.details = payload.details
    
    db.commit()
    db.refresh(analysis)
    
    return {"message": "Analyse mise à jour avec succès"}


@router.delete("/{slug}")
async def delete_analysis(
    slug: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Supprime une analyse."""
    analysis = db.query(Analysis).filter(Analysis.slug == slug).first()
    if analysis:
        assert_same_organization(user, analysis.organization_id)
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analyse non trouvée")
    
    # Gérer les documents liés : soit les supprimer, soit les détacher
    from app.models.analyses import Document
    linked_documents = db.query(Document).filter(Document.analysis_id == analysis.id).all()
    
    # Option 1: Supprimer les documents en cascade (comportement attendu avec ondelete="CASCADE")
    # Les documents seront supprimés automatiquement par la base de données
    # Mais pour éviter les erreurs, on peut les supprimer manuellement d'abord
    for doc in linked_documents:
        db.delete(doc)
    
    # Supprimer l'analyse (les liens GRC seront supprimés en cascade via AnalysisRiskLink)
    db.delete(analysis)
    db.commit()
    
    return {"message": "Analyse supprimée avec succès"}


@router.get("/companies/list")
async def list_companies(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Liste des entreprises de l'organisation."""
    query = db.query(Company)
    if not user.is_platform_admin:
        query = query.filter(Company.organization_id == user.organization_id)
    companies = query.order_by(Company.created_at.desc()).all()
    
    return {
        "companies": [
            {
                "id": c.id,
                "slug": c.slug,
                "nom": c.name,
                "rcs": c.rcs,
                "type": c.company_type,
                "risque": c.risk,
                "qualite": c.quality,
                "score_total": c.total_score,
                "details": c.details or [],
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in companies
        ]
    }

