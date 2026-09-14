"""Proposition de preuves à partir des findings — best-effort, jamais bloquant."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.database import SessionLocal
from app.models.analysis_jobs import AnalysisFinding, AnalysisJob
from app.models.applicability import ApplicabilityDecision
from app.models.compliance_evidence import ComplianceEvidence
from app.services.analysis_jobs import now_utc

logger = logging.getLogger(__name__)

EVIDENCE_SEVERITIES = {"medium", "high", "critical"}
REVIEW_STATUSES = {"accepted", "rejected"}
TREATMENT_STRATEGIES = {"mitigate", "accept", "transfer", "avoid"}
TREATMENT_STATUSES = {"planned", "in_progress", "completed", "cancelled"}


def applicable_frameworks_for(db, organization_id) -> List[str]:
    if not organization_id:
        return ["iso31000"]
    rows = (
        db.query(ApplicabilityDecision)
        .filter(
            ApplicabilityDecision.organization_id == organization_id,
            ApplicabilityDecision.applicable.is_(True),
        )
        .all()
    )
    codes = [row.framework_code for row in rows if row.framework_code]
    return codes or ["iso31000"]


def should_propose(severity: Optional[str]) -> bool:
    return (severity or "").lower() in EVIDENCE_SEVERITIES


def propose_evidence_from_job(job_id: Optional[UUID]) -> int:
    """Crée des preuves proposées pour les findings medium+ d'un job. Retourne le nombre créé."""
    if not job_id:
        return 0
    db = SessionLocal()
    created = 0
    try:
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        if not job:
            return 0
        frameworks = applicable_frameworks_for(db, job.organization_id)
        findings = (
            db.query(AnalysisFinding)
            .filter(AnalysisFinding.job_id == job.id)
            .all()
        )
        existing_ids = {
            row.finding_id
            for row in db.query(ComplianceEvidence.finding_id)
            .filter(ComplianceEvidence.job_id == job.id)
            .all()
            if row.finding_id
        }
        for finding in findings:
            if finding.id in existing_ids or not should_propose(finding.severity):
                continue
            db.add(ComplianceEvidence(
                organization_id=job.organization_id,
                finding_id=finding.id,
                job_id=job.id,
                analysis_id=job.analysis_id,
                framework_code=frameworks[0],
                applicable_frameworks=frameworks,
                title=finding.title,
                detail=finding.detail,
                severity=finding.severity,
                status="proposed",
            ))
            created += 1
        if created:
            db.commit()
        return created
    except Exception as exc:
        db.rollback()
        logger.warning("Impossible de proposer des preuves pour le job %s: %s", job_id, exc)
        return 0
    finally:
        db.close()


def evidence_to_dict(row) -> Dict[str, Any]:
    return {
        "id": str(row.id),
        "finding_id": str(row.finding_id) if row.finding_id else None,
        "job_id": str(row.job_id) if row.job_id else None,
        "analysis_id": str(row.analysis_id) if row.analysis_id else None,
        "framework_code": row.framework_code,
        "applicable_frameworks": row.applicable_frameworks or [],
        "title": row.title,
        "detail": row.detail,
        "severity": row.severity,
        "status": row.status,
        "reviewed_at": row.reviewed_at.isoformat() if row.reviewed_at else None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def treatment_to_dict(row) -> Dict[str, Any]:
    return {
        "id": str(row.id),
        "risk_id": str(row.risk_id),
        "strategy": row.strategy,
        "description": row.description,
        "status": row.status,
        "owner_id": str(row.owner_id) if row.owner_id else None,
        "due_date": row.due_date.isoformat() if row.due_date else None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def review_evidence(row: ComplianceEvidence, status: str, user_id) -> ComplianceEvidence:
    if status not in REVIEW_STATUSES:
        raise ValueError("Statut de revue invalide")
    row.status = status
    row.reviewed_by = user_id
    row.reviewed_at = now_utc()
    return row
