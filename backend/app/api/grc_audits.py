"""Audits GRC isolés par organisation."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.permissions import assert_same_organization, get_current_user
from app.database import get_db
from app.models.grc_audits import AuditFinding, GrcAudit
from app.models.organizations import User
from app.services.grc_audits import (
    AUDIT_TYPES,
    FINDING_SEVERITIES,
    FINDING_STATUSES,
    audit_to_dict,
    finding_to_dict,
    import_accepted_evidence,
)

router = APIRouter(prefix="/api/v1/audits", tags=["audits"])


class AuditCreate(BaseModel):
    title: str
    audit_type: str = "internal"
    framework_code: Optional[str] = None
    scope: Optional[str] = None
    auditor_name: Optional[str] = None


class FindingCreate(BaseModel):
    title: str
    detail: Optional[str] = None
    severity: str = "medium"
    status: str = "open"


def _get_audit(db: Session, audit_id: str, user: User) -> GrcAudit:
    audit = db.query(GrcAudit).filter(GrcAudit.id == audit_id).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit introuvable")
    assert_same_organization(user, audit.organization_id)
    return audit


@router.get("")
async def list_audits(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(GrcAudit)
    if not user.is_platform_admin:
        query = query.filter(GrcAudit.organization_id == user.organization_id)
    rows = query.order_by(GrcAudit.created_at.desc()).limit(50).all()
    return {"audits": [audit_to_dict(row) for row in rows]}


@router.post("", status_code=201)
async def create_audit(
    body: AuditCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if body.audit_type not in AUDIT_TYPES:
        raise HTTPException(status_code=400, detail="Type d'audit invalide")
    if not user.organization_id:
        raise HTTPException(status_code=400, detail="Aucune organisation associée")
    audit = GrcAudit(
        organization_id=user.organization_id,
        title=body.title.strip(),
        audit_type=body.audit_type,
        framework_code=body.framework_code,
        scope=body.scope,
        auditor_name=body.auditor_name,
        status="planned",
        created_by=user.id,
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)
    return audit_to_dict(audit, [])


@router.get("/{audit_id}")
async def get_audit(
    audit_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    audit = _get_audit(db, audit_id, user)
    findings = (
        db.query(AuditFinding)
        .filter(AuditFinding.audit_id == audit.id)
        .order_by(AuditFinding.created_at.asc())
        .all()
    )
    return audit_to_dict(audit, findings)


@router.post("/{audit_id}/findings", status_code=201)
async def add_finding(
    audit_id: str,
    body: FindingCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if body.severity not in FINDING_SEVERITIES:
        raise HTTPException(status_code=400, detail="Sévérité invalide")
    if body.status not in FINDING_STATUSES:
        raise HTTPException(status_code=400, detail="Statut invalide")
    audit = _get_audit(db, audit_id, user)
    if audit.status == "planned":
        audit.status = "in_progress"
    row = AuditFinding(
        audit_id=audit.id,
        organization_id=audit.organization_id,
        title=body.title.strip(),
        detail=body.detail,
        severity=body.severity,
        status=body.status,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return finding_to_dict(row)


@router.post("/{audit_id}/import-evidence")
async def import_evidence(
    audit_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    audit = _get_audit(db, audit_id, user)
    created = import_accepted_evidence(db, audit)
    return {"created": created}
