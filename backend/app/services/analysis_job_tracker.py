"""Écriture best-effort des jobs — ne doit jamais faire échouer /analyser/."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from uuid import UUID

from app.database import SessionLocal
from app.models.analysis_jobs import AnalysisFinding, AnalysisJob
from app.services.analysis_jobs import extract_findings, now_utc, transition

logger = logging.getLogger(__name__)


def _session():
    return SessionLocal()


def start_job(
    *,
    organization_id,
    user_id,
    filename: str,
    storage_key: str,
    slug: Optional[str] = None,
) -> Optional[UUID]:
    if not organization_id:
        return None
    db = _session()
    try:
        job = AnalysisJob(
            organization_id=organization_id,
            user_id=user_id,
            filename=filename,
            storage_key=storage_key,
            slug=slug,
            status="running",
            started_at=now_utc(),
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job.id
    except Exception as exc:
        db.rollback()
        logger.warning("Impossible de créer analysis_job: %s", exc)
        return None
    finally:
        db.close()


def complete_job(
    job_id: Optional[UUID],
    *,
    slug: str,
    analysis_id=None,
    result_summary: Optional[Dict[str, Any]] = None,
    details=None,
) -> None:
    if not job_id:
        return
    db = _session()
    try:
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        if not job:
            return
        job.status = transition(job.status, "completed")
        job.slug = slug
        job.analysis_id = analysis_id
        job.result_summary = result_summary or {}
        job.finished_at = now_utc()
        job.error_message = None
        db.query(AnalysisFinding).filter(AnalysisFinding.job_id == job.id).delete()
        for item in extract_findings(details):
            db.add(AnalysisFinding(
                job_id=job.id,
                organization_id=job.organization_id,
                title=item["title"],
                detail=item["detail"],
                severity=item["severity"],
                score=item["score"],
                source_question=item["source_question"],
                evidence=item["evidence"],
            ))
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.warning("Impossible de terminer analysis_job %s: %s", job_id, exc)
    finally:
        db.close()
    try:
        from app.services.compliance_evidence import propose_evidence_from_job
        propose_evidence_from_job(job_id)
    except Exception as exc:
        logger.warning("Impossible de proposer des preuves pour le job %s: %s", job_id, exc)


def attach_analysis(job_id: Optional[UUID], analysis_id, *, slug: Optional[str] = None) -> None:
    if not job_id or not analysis_id:
        return
    db = _session()
    try:
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        if not job:
            return
        job.analysis_id = analysis_id
        if slug:
            job.slug = slug
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.warning("Impossible de lier analysis_job %s: %s", job_id, exc)
    finally:
        db.close()


def cancel_job_for_slug(organization_id, slug: str) -> bool:
    if not organization_id or not slug:
        return False
    db = _session()
    try:
        job = (
            db.query(AnalysisJob)
            .filter(
                AnalysisJob.organization_id == organization_id,
                AnalysisJob.slug == slug,
                AnalysisJob.status.in_(["queued", "running"]),
            )
            .order_by(AnalysisJob.created_at.desc())
            .first()
        )
        if not job:
            return False
        job.status = transition(job.status, "cancelled")
        job.finished_at = now_utc()
        db.commit()
        return True
    except Exception as exc:
        db.rollback()
        logger.warning("Impossible d'annuler analysis_job slug=%s: %s", slug, exc)
        return False
    finally:
        db.close()


def fail_job(job_id: Optional[UUID], error_message: str) -> None:
    if not job_id:
        return
    db = _session()
    try:
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        if not job:
            return
        job.status = transition(job.status, "failed")
        job.error_message = (error_message or "Erreur d'analyse")[:2000]
        job.finished_at = now_utc()
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.warning("Impossible de marquer analysis_job failed %s: %s", job_id, exc)
    finally:
        db.close()
