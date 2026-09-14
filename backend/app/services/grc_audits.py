"""Helpers audits GRC + import des preuves acceptées."""

from __future__ import annotations

from typing import Any, Dict, List

from app.models.compliance_evidence import ComplianceEvidence
from app.models.grc_audits import AuditFinding, GrcAudit

AUDIT_TYPES = {"internal", "external", "self_assessment"}
AUDIT_STATUSES = {"planned", "in_progress", "completed", "cancelled"}
FINDING_STATUSES = {"open", "in_progress", "closed"}
FINDING_SEVERITIES = {"low", "medium", "high", "critical"}


def audit_to_dict(audit: GrcAudit, findings: List[AuditFinding] = None) -> Dict[str, Any]:
    payload = {
        "id": str(audit.id),
        "title": audit.title,
        "audit_type": audit.audit_type,
        "framework_code": audit.framework_code,
        "status": audit.status,
        "scope": audit.scope,
        "auditor_name": audit.auditor_name,
        "started_at": audit.started_at.isoformat() if audit.started_at else None,
        "finished_at": audit.finished_at.isoformat() if audit.finished_at else None,
        "created_at": audit.created_at.isoformat() if audit.created_at else None,
    }
    if findings is not None:
        payload["findings"] = [finding_to_dict(row) for row in findings]
        payload["findings_count"] = len(findings)
    return payload


def finding_to_dict(row: AuditFinding) -> Dict[str, Any]:
    return {
        "id": str(row.id),
        "audit_id": str(row.audit_id),
        "evidence_id": str(row.evidence_id) if row.evidence_id else None,
        "title": row.title,
        "detail": row.detail,
        "severity": row.severity,
        "status": row.status,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def import_accepted_evidence(db, audit: GrcAudit) -> int:
    """Copie les preuves acceptées de l'orga en findings. Idempotent par evidence_id."""
    existing = {
        row.evidence_id
        for row in db.query(AuditFinding.evidence_id)
        .filter(AuditFinding.audit_id == audit.id)
        .all()
        if row.evidence_id
    }
    proofs = (
        db.query(ComplianceEvidence)
        .filter(
            ComplianceEvidence.organization_id == audit.organization_id,
            ComplianceEvidence.status == "accepted",
        )
        .all()
    )
    created = 0
    for proof in proofs:
        if proof.id in existing:
            continue
        db.add(AuditFinding(
            audit_id=audit.id,
            organization_id=audit.organization_id,
            evidence_id=proof.id,
            title=proof.title,
            detail=proof.detail,
            severity=proof.severity if proof.severity in FINDING_SEVERITIES else "medium",
            status="open",
        ))
        created += 1
    if created:
        db.commit()
    return created
