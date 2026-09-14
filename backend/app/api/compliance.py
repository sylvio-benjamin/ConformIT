"""
API REST pour la gestion de la conformité.
Endpoints : GET /api/compliance/frameworks, GET /api/compliance/assessments, POST /api/compliance/assessments, etc.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Optional, Dict, Any
from uuid import UUID as PyUUID
from datetime import datetime, timedelta

from app.database import get_db
from app.models.compliance import (
    ComplianceFramework, ComplianceAssessment, ComplianceRequirement,
    ComplianceGap, ComplianceRemediation
)
from app.models.organizations import Organization, User
from app.core.permissions import get_current_user

router = APIRouter(prefix="/api/compliance", tags=["compliance"])


def _organization_of(db: Session, current: User) -> Organization:
    if not current.organization_id:
        raise HTTPException(status_code=400, detail="Aucune organisation associée")
    org = db.query(Organization).filter(Organization.id == current.organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organisation introuvable")
    return org


@router.get("/frameworks")
async def list_frameworks(db: Session = Depends(get_db)):
    """Liste des cadres de conformité."""
    frameworks = db.query(ComplianceFramework).filter(ComplianceFramework.is_active == True).all()
    return [{"id": str(f.id), "name": f.name, "code": f.code, "description": f.description} for f in frameworks]


@router.get("/frameworks/{framework_id}")
async def get_framework(framework_id: str, db: Session = Depends(get_db)):
    """Détails d'un cadre de conformité."""
    try:
        framework = db.query(ComplianceFramework).filter(ComplianceFramework.id == PyUUID(framework_id)).first()
        if not framework:
            raise HTTPException(status_code=404, detail="Cadre de conformité non trouvé")
        return {"id": str(framework.id), "name": framework.name, "code": framework.code, "description": framework.description}
    except ValueError:
        raise HTTPException(status_code=400, detail="ID invalide")


@router.get("/assessments")
async def list_assessments(
    current: User = Depends(get_current_user),
    framework_id: Optional[str] = Query(None, description="Filtrer par cadre de conformité"),
    db: Session = Depends(get_db)
):
    """Liste des évaluations de conformité."""
    org = _organization_of(db, current)
    query = db.query(ComplianceAssessment).filter(ComplianceAssessment.organization_id == org.id)
    
    if framework_id:
        query = query.filter(ComplianceAssessment.framework_id == PyUUID(framework_id))
    
    assessments = query.all()
    return [
        {
            "id": str(a.id),
            "framework_id": str(a.framework_id) if a.framework_id else None,
            "compliance_status": a.compliance_status,
            "assessment_date": a.assessment_date.isoformat() if a.assessment_date else None,
        }
        for a in assessments
    ]


@router.get("/dashboard/scores")
async def get_compliance_scores(
    current: User = Depends(get_current_user),
    period: Optional[str] = Query("monthly", description="Période: daily, weekly, monthly, quarterly"),
    db: Session = Depends(get_db)
):
    """
    Récupère les scores de conformité pour les graphiques.
    Retourne le score global et les scores par norme.
    """
    org = _organization_of(db, current)
    
    # Récupérer tous les frameworks
    frameworks = db.query(ComplianceFramework).filter(ComplianceFramework.is_active == True).all()
    
    # Calculer les scores par framework
    scores_by_framework = []
    total_score = 0
    assessed_count = 0
    
    for framework in frameworks:
        # Récupérer les assessments pour ce framework
        assessments = db.query(ComplianceAssessment).filter(
            and_(
                ComplianceAssessment.organization_id == org.id,
                ComplianceAssessment.framework_id == framework.id
            )
        ).all()
        
        if assessments:
            # Calculer le score moyen (basé sur les statuts: compliant=100, partially_compliant=50, non_compliant=0)
            status_scores = {
                "compliant": 100,
                "partially_compliant": 50,
                "non_compliant": 0,
                "not_applicable": 0
            }
            
            avg_score = sum(status_scores.get(a.compliance_status, 0) for a in assessments) / len(assessments)
            scores_by_framework.append({
                "framework_id": str(framework.id),
                "framework_name": framework.name,
                "framework_code": framework.code,
                "score": round(avg_score, 2),
                "status": "assessed"
            })
            total_score += avg_score
            assessed_count += 1
        else:
            scores_by_framework.append({
                "framework_id": str(framework.id),
                "framework_name": framework.name,
                "framework_code": framework.code,
                "score": 0,
                "status": "not_assessed"
            })
    
    # Score global
    overall_score = round(total_score / assessed_count, 2) if assessed_count > 0 else 0
    
    return {
        "overall_score": overall_score,
        "scores_by_framework": scores_by_framework,
        "total_frameworks": len(frameworks),
        "assessed_frameworks": assessed_count
    }


@router.get("/dashboard/evolution")
async def get_compliance_evolution(
    current: User = Depends(get_current_user),
    framework_id: Optional[str] = Query(None, description="ID du cadre de conformité (optionnel)"),
    period: str = Query("monthly", description="Période: daily, weekly, monthly, quarterly"),
    months: int = Query(12, description="Nombre de mois d'historique"),
    db: Session = Depends(get_db)
):
    """
    Récupère l'évolution des scores de conformité dans le temps.
    """
    org = _organization_of(db, current)
    
    # Déterminer la période de groupement
    if period == "daily":
        date_format = "%Y-%m-%d"
        delta = timedelta(days=1)
    elif period == "weekly":
        date_format = "%Y-%W"
        delta = timedelta(weeks=1)
    elif period == "quarterly":
        date_format = "%Y-Q%q"
        delta = timedelta(days=90)
    else:  # monthly
        date_format = "%Y-%m"
        delta = timedelta(days=30)
    
    # Date de début
    start_date = datetime.utcnow() - timedelta(days=months * 30)
    
    # Récupérer toutes les assessments dans la période
    query = db.query(ComplianceAssessment).filter(
        and_(
            ComplianceAssessment.organization_id == org.id,
            ComplianceAssessment.assessment_date >= start_date
        )
    )
    
    if framework_id:
        query = query.filter(ComplianceAssessment.framework_id == PyUUID(framework_id))
    
    assessments = query.all()
    
    # Calculer les scores par période et framework
    evolution_data = {}
    status_scores = {"compliant": 100, "partially_compliant": 50, "non_compliant": 0, "not_applicable": 0}
    
    for assessment in assessments:
        if not assessment.assessment_date:
            continue
            
        # Formater la période selon le format choisi
        if period == "daily":
            period_str = assessment.assessment_date.strftime("%Y-%m-%d")
        elif period == "weekly":
            period_str = f"{assessment.assessment_date.year}-W{assessment.assessment_date.isocalendar()[1]:02d}"
        elif period == "quarterly":
            quarter = (assessment.assessment_date.month - 1) // 3 + 1
            period_str = f"{assessment.assessment_date.year}-Q{quarter}"
        else:  # monthly
            period_str = assessment.assessment_date.strftime("%Y-%m")
        
        framework_id_str = str(assessment.framework_id) if assessment.framework_id else "global"
        
        if framework_id_str not in evolution_data:
            evolution_data[framework_id_str] = {}
        
        if period_str not in evolution_data[framework_id_str]:
            evolution_data[framework_id_str][period_str] = {"scores": [], "count": 0}
        
        score = status_scores.get(assessment.compliance_status, 0)
        evolution_data[framework_id_str][period_str]["scores"].append(score)
        evolution_data[framework_id_str][period_str]["count"] += 1
    
    # Calculer les moyennes et formater
    formatted_evolution = {}
    for fw_id, periods in evolution_data.items():
        formatted_evolution[fw_id] = []
        for period_str, data in sorted(periods.items()):
            avg_score = sum(data["scores"]) / len(data["scores"]) if data["scores"] else 0
            formatted_evolution[fw_id].append({
                "period": period_str,
                "score": round(avg_score, 2)
            })
    
    return {
        "evolution": formatted_evolution,
        "period": period,
        "months": months
    }


@router.get("/dashboard/matrix")
async def get_compliance_risk_matrix(
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupère les données pour la matrice conformité/risque.
    """
    from app.models.risks import Risk
    
    org = _organization_of(db, current)
    
    # Récupérer les risques
    risks = db.query(Risk).filter(Risk.organization_id == org.id).all()
    
    # Récupérer les scores de conformité par framework
    frameworks = db.query(ComplianceFramework).filter(ComplianceFramework.is_active == True).all()
    
    # Calculer les scores de conformité
    compliance_scores = {}
    for framework in frameworks:
        assessments = db.query(ComplianceAssessment).filter(
            and_(
                ComplianceAssessment.organization_id == org.id,
                ComplianceAssessment.framework_id == framework.id
            )
        ).all()
        
        if assessments:
            status_scores = {"compliant": 100, "partially_compliant": 50, "non_compliant": 0}
            avg_score = sum(status_scores.get(a.compliance_status, 0) for a in assessments) / len(assessments)
            compliance_scores[framework.code] = round(avg_score, 2)
        else:
            compliance_scores[framework.code] = 0
    
    # Calculer le niveau de risque moyen (basé sur la priorité)
    risk_scores = {"low": 25, "medium": 50, "high": 75, "critical": 100}
    risk_levels = [risk_scores.get(risk.priority, 0) for risk in risks if risk.priority]
    avg_risk_level = round(sum(risk_levels) / len(risk_levels), 2) if risk_levels else 0
    
    # Score global de conformité
    overall_compliance = round(sum(compliance_scores.values()) / len(compliance_scores), 2) if compliance_scores else 0
    
    return {
        "compliance_score": overall_compliance,
        "risk_level": avg_risk_level,
        "compliance_by_framework": compliance_scores,
        "risk_count": len(risks),
        "critical_risks": len([r for r in risks if r.priority == "critical"])
    }


@router.get("/dashboard/actions")
async def get_remediation_actions(
    current: User = Depends(get_current_user),
    status: Optional[str] = Query(None, description="Filtrer par statut"),
    db: Session = Depends(get_db)
):
    """
    Récupère les actions correctives (remediation) pour les graphiques.
    """
    org = _organization_of(db, current)
    
    # Récupérer tous les gaps avec leurs remediations
    from app.models.compliance import ComplianceGap
    gaps = db.query(ComplianceGap).join(ComplianceAssessment).filter(
        ComplianceAssessment.organization_id == org.id
    ).all()
    
    remediations = []
    for gap in gaps:
        if gap.remediation:
            rem = gap.remediation
            remediations.append({
                "id": str(rem.id),
                "title": rem.title,
                "status": rem.status,
                "due_date": rem.due_date.isoformat() if rem.due_date else None,
                "completed_at": rem.completed_at.isoformat() if rem.completed_at else None,
                "created_at": rem.created_at.isoformat() if rem.created_at else None,
                "gap_severity": gap.severity,
                "gap_id": str(gap.id)
            })
    
    if status:
        remediations = [r for r in remediations if r["status"] == status]
    
    # Statistiques par statut
    status_counts = {}
    for rem in remediations:
        s = rem["status"]
        status_counts[s] = status_counts.get(s, 0) + 1
    
    return {
        "remediations": remediations,
        "status_counts": status_counts,
        "total": len(remediations)
    }


@router.get("/dashboard/heatmap")
async def get_compliance_heatmap(
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupère les données pour la carte thermique de conformité.
    """
    org = _organization_of(db, current)
    
    frameworks = db.query(ComplianceFramework).filter(ComplianceFramework.is_active == True).all()
    
    heatmap_data = []
    for framework in frameworks:
        assessments = db.query(ComplianceAssessment).filter(
            and_(
                ComplianceAssessment.organization_id == org.id,
                ComplianceAssessment.framework_id == framework.id
            )
        ).all()
        
        if assessments:
            status_scores = {"compliant": 100, "partially_compliant": 50, "non_compliant": 0}
            avg_score = sum(status_scores.get(a.compliance_status, 0) for a in assessments) / len(assessments)
            
            # Compter les gaps
            from app.models.compliance import ComplianceGap
            gaps = db.query(ComplianceGap).join(ComplianceAssessment).filter(
                ComplianceAssessment.id.in_([a.id for a in assessments])
            ).all()
            
            critical_gaps = len([g for g in gaps if g.severity == "critical"])
            high_gaps = len([g for g in gaps if g.severity == "high"])
            
            heatmap_data.append({
                "framework_id": str(framework.id),
                "framework_name": framework.name,
                "framework_code": framework.code,
                "score": round(avg_score, 2),
                "critical_gaps": critical_gaps,
                "high_gaps": high_gaps,
                "total_gaps": len(gaps),
                "assessments_count": len(assessments)
            })
        else:
            heatmap_data.append({
                "framework_id": str(framework.id),
                "framework_name": framework.name,
                "framework_code": framework.code,
                "score": 0,
                "critical_gaps": 0,
                "high_gaps": 0,
                "total_gaps": 0,
                "assessments_count": 0
            })
    
    return {
        "heatmap_data": heatmap_data,
        "max_score": max([d["score"] for d in heatmap_data], default=100),
        "min_score": min([d["score"] for d in heatmap_data], default=0)
    }


@router.get("/dashboard/gaps")
async def get_compliance_gaps(
    current: User = Depends(get_current_user),
    framework_id: Optional[str] = Query(None, description="Filtrer par framework"),
    db: Session = Depends(get_db)
):
    """
    Récupère les écarts de conformité (gaps).
    """
    org = _organization_of(db, current)
    
    from app.models.compliance import ComplianceGap
    
    query = db.query(ComplianceGap).join(ComplianceAssessment).filter(
        ComplianceAssessment.organization_id == org.id
    )
    
    if framework_id:
        query = query.filter(ComplianceAssessment.framework_id == PyUUID(framework_id))
    
    gaps = query.all()
    
    # Groupement par sévérité
    severity_counts = {}
    for gap in gaps:
        sev = gap.severity or "unknown"
        severity_counts[sev] = severity_counts.get(sev, 0) + 1
    
    # Groupement par framework
    framework_gaps = {}
    for gap in gaps:
        if gap.assessment and gap.assessment.framework:
            fw_code = gap.assessment.framework.code
            if fw_code not in framework_gaps:
                framework_gaps[fw_code] = 0
            framework_gaps[fw_code] += 1
    
    return {
        "gaps": [
            {
                "id": str(gap.id),
                "description": gap.gap_description,
                "severity": gap.severity,
                "status": gap.status,
                "framework_code": gap.assessment.framework.code if gap.assessment and gap.assessment.framework else None,
                "created_at": gap.created_at.isoformat() if gap.created_at else None
            }
            for gap in gaps
        ],
        "severity_counts": severity_counts,
        "framework_gaps": framework_gaps,
        "total": len(gaps)
    }


@router.post("/assessments")
async def create_assessment():
    """Créer une évaluation de conformité."""
    return {"message": "Assessment created"}

