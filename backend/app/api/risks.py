"""
API REST pour la gestion des risques.
Endpoints : GET /api/risks, GET /api/risks/:id, POST /api/risks, PUT /api/risks/:id, DELETE /api/risks/:id, etc.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from uuid import UUID as PyUUID

from app.database import get_db
from app.models.risks import Risk, RiskCategory, RiskAssessment
from app.models.organizations import User
from app.core.permissions import get_current_user, assert_same_organization
from app.schemas.risks import (
    RiskCreate, RiskUpdate, RiskResponse,
    RiskAssessmentCreate, RiskAssessmentResponse
)

router = APIRouter(prefix="/api/risks", tags=["risks"])


def generate_risk_code(db: Session, organization_id: PyUUID) -> str:
    """Génère un code unique pour un risque (RISK-001, RISK-002, etc.)."""
    count = db.query(Risk).filter(Risk.organization_id == organization_id).count()
    return f"RISK-{count + 1:03d}"


@router.get("", response_model=List[RiskResponse])
async def list_risks(
    status: Optional[str] = Query(None, description="Filtrer par statut"),
    priority: Optional[str] = Query(None, description="Filtrer par priorité"),
    search: Optional[str] = Query(None, description="Recherche dans le titre et la description"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Liste des risques de l'organisation de l'utilisateur."""
    query = db.query(Risk)
    if not user.is_platform_admin:
        query = query.filter(Risk.organization_id == user.organization_id)
    
    if status:
        query = query.filter(Risk.status == status)
    
    if priority:
        query = query.filter(Risk.priority == priority)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Risk.title.ilike(search_pattern),
                Risk.description.ilike(search_pattern)
            )
        )
    
    risks = query.all()
    return risks


@router.get("/{risk_id}", response_model=RiskResponse)
async def get_risk(
    risk_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Détails d'un risque."""
    try:
        risk = db.query(Risk).filter(Risk.id == PyUUID(risk_id)).first()
        if not risk:
            raise HTTPException(status_code=404, detail="Risque non trouvé")
        assert_same_organization(user, risk.organization_id)
        return risk
    except ValueError:
        raise HTTPException(status_code=400, detail="ID invalide")


@router.post("", response_model=RiskResponse, status_code=201)
async def create_risk(
    risk_data: RiskCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Créer un risque dans l'organisation de l'utilisateur."""
    if not user.organization_id:
        raise HTTPException(status_code=400, detail="Aucune organisation associée")
    org_id = user.organization_id
    
    # Générer le code unique
    code = generate_risk_code(db, org_id)
    
    # Créer le risque
    risk = Risk(
        organization_id=org_id,
        code=code,
        title=risk_data.title,
        description=risk_data.description,
        category_id=PyUUID(risk_data.category_id) if risk_data.category_id else None,
        owner_id=PyUUID(risk_data.owner_id) if risk_data.owner_id else None,
        parent_risk_id=PyUUID(risk_data.parent_risk_id) if risk_data.parent_risk_id else None,
        priority=risk_data.priority,
        tags=risk_data.tags or [],
        meta_data=risk_data.metadata or {},
        created_by=user.id,
    )
    
    db.add(risk)
    db.commit()
    db.refresh(risk)
    
    return risk


@router.put("/{risk_id}", response_model=RiskResponse)
async def update_risk(
    risk_id: str,
    risk_data: RiskUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Mettre à jour un risque."""
    try:
        risk = db.query(Risk).filter(Risk.id == PyUUID(risk_id)).first()
        if not risk:
            raise HTTPException(status_code=404, detail="Risque non trouvé")
        assert_same_organization(user, risk.organization_id)
        
        # Mettre à jour les champs fournis
        update_data = risk_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            if key == "category_id" and value:
                value = PyUUID(value)
            elif key == "owner_id" and value:
                value = PyUUID(value)
            elif key == "parent_risk_id" and value:
                value = PyUUID(value)
            setattr(risk, key, value)
        
        db.commit()
        db.refresh(risk)
        
        return risk
    except ValueError:
        raise HTTPException(status_code=400, detail="ID invalide")


@router.delete("/{risk_id}", status_code=204)
async def delete_risk(
    risk_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Supprimer un risque."""
    try:
        risk = db.query(Risk).filter(Risk.id == PyUUID(risk_id)).first()
        if not risk:
            raise HTTPException(status_code=404, detail="Risque non trouvé")
        assert_same_organization(user, risk.organization_id)
        
        db.delete(risk)
        db.commit()
        return None
    except ValueError:
        raise HTTPException(status_code=400, detail="ID invalide")


@router.post("/{risk_id}/assessments", response_model=RiskAssessmentResponse, status_code=201)
async def create_assessment(
    risk_id: str,
    assessment_data: RiskAssessmentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Créer une évaluation de risque."""
    try:
        # Vérifier que le risque existe
        risk = db.query(Risk).filter(Risk.id == PyUUID(risk_id)).first()
        if not risk:
            raise HTTPException(status_code=404, detail="Risque non trouvé")
        assert_same_organization(user, risk.organization_id)
        
        # Calculer le niveau de risque et le score
        # Formule simple : (probability_level * impact_level) / 25 * 100
        risk_score = int((assessment_data.probability_level * assessment_data.impact_level) / 25 * 100)
        
        # Déterminer le niveau de risque
        if risk_score >= 80:
            risk_level = "critical"
        elif risk_score >= 60:
            risk_level = "high"
        elif risk_score >= 40:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        assessment = RiskAssessment(
            risk_id=PyUUID(risk_id),
            probability_level=assessment_data.probability_level,
            impact_level=assessment_data.impact_level,
            risk_level=risk_level,
            risk_score=risk_score,
            methodology=assessment_data.methodology or "qualitative",
            justification=assessment_data.justification,
            confidence_level=assessment_data.confidence_level or 5
        )
        
        db.add(assessment)
        
        # Mettre à jour le statut du risque
        risk.status = "assessed"
        
        db.commit()
        db.refresh(assessment)
        
        return assessment
    except ValueError:
        raise HTTPException(status_code=400, detail="ID invalide")
