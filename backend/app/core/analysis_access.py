"""Contrôle d'accès aux analyses par slug — état SQL uniquement (analysis + analysis_jobs)."""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.analyses import Analysis
from app.models.analysis_jobs import AnalysisJob
from app.models.organizations import User


def assert_slug_access(db: Session, user: User, slug: str) -> None:
    analysis = db.query(Analysis).filter(Analysis.slug == slug).first()
    if analysis:
        if not user.is_platform_admin and analysis.organization_id != user.organization_id:
            raise HTTPException(status_code=403, detail="Accès refusé à cette analyse")
        return
    job = (
        db.query(AnalysisJob)
        .filter(AnalysisJob.slug == slug)
        .order_by(AnalysisJob.created_at.desc())
        .first()
    )
    if job:
        if not user.is_platform_admin and job.organization_id != user.organization_id:
            raise HTTPException(status_code=403, detail="Accès refusé à cette analyse")
        return
    raise HTTPException(status_code=404, detail="Analyse introuvable")
