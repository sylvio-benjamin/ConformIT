"""
API REST pour l'intégration Analyse → GRC.
Endpoints pour déclencher et gérer l'intégration des analyses avec la GRC.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from uuid import UUID as PyUUID

from app.database import get_db
from app.models.analyses import Analysis
from app.models.risks import Risk
from app.models.analysis_risk_link import AnalysisRiskLink, RiskHistory
from app.services.analysis_grc_integration import AnalysisGRCIntegrationService
from app.models.organizations import User
from app.core.permissions import get_current_user, assert_same_organization

router = APIRouter(prefix="/api/analysis-grc", tags=["analysis-grc"])


@router.post("/integrate/{analysis_id}")
async def integrate_analysis_to_grc(
    analysis_id: str,
    force: bool = Query(False, description="Forcer la réintégration même si déjà intégrée"),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """
    Intègre une analyse dans la GRC en créant ou mettant à jour les risques.
    
    Cette fonction:
    - Extrait les findings de l'analyse
    - Trouve les risques similaires existants
    - Crée de nouveaux risques ou met à jour les risques existants
    - Lie l'analyse aux risques créés/mis à jour
    """
    try:
        service = AnalysisGRCIntegrationService(db)
        result = service.integrate_analysis_to_grc(
            analysis_id=analysis_id,
            user_id=str(current.id),
            force=force
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'intégration: {str(e)}")


@router.get("/analysis/{analysis_id}/risks")
async def get_risks_from_analysis(
    analysis_id: str,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """
    Récupère les risques GRC liés à une analyse.
    """
    # Vérifier l'analyse
    if len(analysis_id) > 20:
        # UUID
        analysis = db.query(Analysis).filter(Analysis.id == PyUUID(analysis_id)).first()
    else:
        # Slug
        analysis = db.query(Analysis).filter(Analysis.slug == analysis_id).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analyse non trouvée")
    
    assert_same_organization(current, analysis.organization_id)
    
    # Récupérer les liens
    links = db.query(AnalysisRiskLink).filter(
        AnalysisRiskLink.analysis_id == analysis.id
    ).all()
    
    risks = []
    for link in links:
        risk = db.query(Risk).filter(Risk.id == link.risk_id).first()
        if risk:
            risks.append({
                "risk_id": str(risk.id),
                "risk_code": risk.code,
                "title": risk.title,
                "priority": risk.priority,
                "status": risk.status,
                "link_id": str(link.id),
                "integration_status": link.integration_status,
                "finding_severity": link.severity,
                "created_at": link.created_at.isoformat() if link.created_at else None
            })
    
    return {
        "analysis_id": str(analysis.id),
        "analysis_slug": analysis.slug,
        "risks": risks,
        "count": len(risks)
    }


@router.get("/risk/{risk_id}/analyses")
async def get_analyses_from_risk(
    risk_id: str,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """
    Récupère l'historique des analyses liées à un risque GRC.
    """
    # Vérifier le risque
    risk = db.query(Risk).filter(Risk.id == PyUUID(risk_id)).first()
    if not risk:
        raise HTTPException(status_code=404, detail="Risque non trouvé")
    
    assert_same_organization(current, risk.organization_id)
    
    # Récupérer les liens
    links = db.query(AnalysisRiskLink).filter(
        AnalysisRiskLink.risk_id == risk.id
    ).order_by(AnalysisRiskLink.created_at.desc()).all()
    
    analyses = []
    for link in links:
        analysis = db.query(Analysis).filter(Analysis.id == link.analysis_id).first()
        if analysis:
            analyses.append({
                "analysis_id": str(analysis.id),
                "analysis_slug": analysis.slug,
                "analysis_number": analysis.analysis_number,
                "company_name": analysis.company_name,
                "document_type": analysis.document_type,
                "score": analysis.total_score,
                "risk_level": analysis.risk_level,
                "link_id": str(link.id),
                "integration_status": link.integration_status,
                "finding_severity": link.severity,
                "created_at": link.created_at.isoformat() if link.created_at else None
            })
    
    # Récupérer l'historique du risque
    histories = db.query(RiskHistory).filter(
        RiskHistory.risk_id == risk.id,
        RiskHistory.analysis_id.isnot(None)
    ).order_by(RiskHistory.created_at.desc()).all()
    
    history_entries = []
    for hist in histories:
        history_entries.append({
            "change_type": hist.change_type,
            "description": hist.description,
            "old_value": hist.old_value,
            "new_value": hist.new_value,
            "analysis_id": str(hist.analysis_id) if hist.analysis_id else None,
            "changed_at": hist.created_at.isoformat() if hist.created_at else None
        })
    
    return {
        "risk_id": str(risk.id),
        "risk_code": risk.code,
        "risk_title": risk.title,
        "analyses": analyses,
        "analysis_history": risk.analysis_history or [],
        "history_entries": history_entries,
        "total_analyses": len(analyses),
        "linked_analyses_count": risk.linked_analyses_count or 0
    }


@router.post("/auto-integrate")
async def auto_integrate_all_analyses(
    force: bool = Query(False, description="Forcer la réintégration"),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """
    Intègre automatiquement toutes les analyses d'un utilisateur dans la GRC.
    Utile pour une migration ou une réintégration complète.
    """
    analyses = db.query(Analysis).filter(Analysis.employee_id == current.id).all()
    
    service = AnalysisGRCIntegrationService(db)
    results = []
    
    for analysis in analyses:
        try:
            result = service.integrate_analysis_to_grc(
                analysis_id=str(analysis.id),
                user_id=str(current.id),
                force=force
            )
            results.append({
                "analysis_slug": analysis.slug,
                "status": result.get("status"),
                "risks_created": len(result.get("created_risks", [])),
                "risks_updated": len(result.get("updated_risks", []))
            })
        except Exception as e:
            results.append({
                "analysis_slug": analysis.slug,
                "status": "error",
                "error": str(e)
            })
    
    return {
        "status": "completed",
        "total_analyses": len(analyses),
        "results": results,
        "summary": {
            "success": len([r for r in results if r.get("status") == "success"]),
            "errors": len([r for r in results if r.get("status") == "error"]),
            "skipped": len([r for r in results if r.get("status") in ["already_integrated", "no_findings"]])
        }
    }

