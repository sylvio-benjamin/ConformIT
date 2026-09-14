"""Preuves de conformité isolées par organisation."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.permissions import assert_same_organization, get_current_user
from app.database import get_db
from app.models.compliance_evidence import ComplianceEvidence
from app.models.organizations import User
from app.services.compliance_evidence import (
    REVIEW_STATUSES,
    evidence_to_dict,
    propose_evidence_from_job,
    review_evidence,
)

router = APIRouter(prefix="/api/v1/compliance-evidence", tags=["compliance-evidence"])


class ReviewBody(BaseModel):
    status: str


@router.get("")
async def list_evidence(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(ComplianceEvidence)
    if not user.is_platform_admin:
        query = query.filter(ComplianceEvidence.organization_id == user.organization_id)
    if status:
        query = query.filter(ComplianceEvidence.status == status)
    rows = query.order_by(ComplianceEvidence.created_at.desc()).limit(100).all()
    return {"evidence": [evidence_to_dict(row) for row in rows]}


@router.post("/from-job/{job_id}")
async def propose_from_job(
    job_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from app.models.analysis_jobs import AnalysisJob

    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job introuvable")
    assert_same_organization(user, job.organization_id)
    created = propose_evidence_from_job(job.id)
    return {"created": created}


@router.post("/{evidence_id}/review")
async def review(
    evidence_id: str,
    body: ReviewBody,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if body.status not in REVIEW_STATUSES:
        raise HTTPException(status_code=400, detail="Statut invalide (accepted|rejected)")
    row = db.query(ComplianceEvidence).filter(ComplianceEvidence.id == evidence_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Preuve introuvable")
    assert_same_organization(user, row.organization_id)
    review_evidence(row, body.status, user.id)
    db.commit()
    db.refresh(row)
    return evidence_to_dict(row)
