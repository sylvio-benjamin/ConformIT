"""Liste et détail des jobs d'analyse, isolés par organisation."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.permissions import assert_same_organization, get_current_user
from app.database import get_db
from app.models.analysis_jobs import AnalysisFinding, AnalysisJob
from app.models.organizations import User
from app.services.analysis_jobs import job_to_dict

router = APIRouter(prefix="/api/v1/analysis-jobs", tags=["analysis-jobs"])


@router.get("")
async def list_jobs(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(AnalysisJob)
    if not user.is_platform_admin:
        query = query.filter(AnalysisJob.organization_id == user.organization_id)
    jobs = query.order_by(AnalysisJob.created_at.desc()).limit(50).all()
    return {"jobs": [job_to_dict(job) for job in jobs]}


@router.get("/{job_id}")
async def get_job(
    job_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job introuvable")
    assert_same_organization(user, job.organization_id)
    findings = (
        db.query(AnalysisFinding)
        .filter(AnalysisFinding.job_id == job.id)
        .order_by(AnalysisFinding.created_at.asc())
        .all()
    )
    return {
        **job_to_dict(job),
        "findings": [
            {
                "id": str(row.id),
                "title": row.title,
                "detail": row.detail,
                "severity": row.severity,
                "score": row.score,
                "source_question": row.source_question,
                "evidence": row.evidence or {},
            }
            for row in findings
        ],
    }
