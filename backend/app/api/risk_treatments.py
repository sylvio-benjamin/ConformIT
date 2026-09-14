"""Traitements de risques isolés par organisation."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.permissions import assert_same_organization, get_current_user
from app.database import get_db
from app.models.compliance_evidence import RiskTreatment
from app.models.organizations import User
from app.models.risks import Risk
from app.services.compliance_evidence import TREATMENT_STATUSES, TREATMENT_STRATEGIES, treatment_to_dict

router = APIRouter(prefix="/api/v1/risk-treatments", tags=["risk-treatments"])


class TreatmentCreate(BaseModel):
    risk_id: str
    strategy: str
    description: Optional[str] = None
    status: Optional[str] = "planned"
    due_date: Optional[datetime] = None


@router.get("")
async def list_treatments(
    risk_id: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(RiskTreatment)
    if not user.is_platform_admin:
        query = query.filter(RiskTreatment.organization_id == user.organization_id)
    if risk_id:
        query = query.filter(RiskTreatment.risk_id == risk_id)
    rows = query.order_by(RiskTreatment.created_at.desc()).limit(100).all()
    return {"treatments": [treatment_to_dict(row) for row in rows]}


@router.post("", status_code=201)
async def create_treatment(
    body: TreatmentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if body.strategy not in TREATMENT_STRATEGIES:
        raise HTTPException(status_code=400, detail="Stratégie invalide (mitigate|accept|transfer|avoid)")
    status = body.status or "planned"
    if status not in TREATMENT_STATUSES:
        raise HTTPException(status_code=400, detail="Statut invalide")
    if not user.organization_id:
        raise HTTPException(status_code=400, detail="Aucune organisation associée")
    risk = db.query(Risk).filter(Risk.id == body.risk_id).first()
    if not risk:
        raise HTTPException(status_code=404, detail="Risque introuvable")
    assert_same_organization(user, risk.organization_id)
    row = RiskTreatment(
        organization_id=user.organization_id,
        risk_id=risk.id,
        strategy=body.strategy,
        description=body.description,
        status=status,
        owner_id=user.id,
        due_date=body.due_date,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return treatment_to_dict(row)
