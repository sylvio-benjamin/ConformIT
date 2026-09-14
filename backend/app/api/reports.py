"""API rapports GRC, isolée par organisation."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.permissions import assert_same_organization, get_current_user
from app.database import get_db
from app.models.organizations import User
from app.models.reports import Report

router = APIRouter(prefix="/api/reports", tags=["reports"])


class ReportCreate(BaseModel):
    title: str = Field(..., min_length=1)
    report_type: str = Field(default="risk_report")
    file_format: str = Field(default="pdf")


def _to_dict(report: Report) -> dict:
    return {
        "id": str(report.id),
        "title": report.title,
        "name": report.title,
        "type": report.report_type,
        "report_type": report.report_type,
        "status": report.status,
        "file_format": report.file_format,
        "createdAt": report.created_at.isoformat() if report.created_at else None,
        "created_at": report.created_at.isoformat() if report.created_at else None,
    }


@router.get("")
async def list_reports(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(Report)
    if not user.is_platform_admin:
        query = query.filter(Report.organization_id == user.organization_id)
    return {"reports": [_to_dict(r) for r in query.order_by(Report.created_at.desc()).all()]}


@router.post("", status_code=201)
async def create_report(
    payload: ReportCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user.organization_id:
        raise HTTPException(status_code=400, detail="Aucune organisation associée")
    report = Report(
        organization_id=user.organization_id,
        title=payload.title,
        report_type=payload.report_type,
        file_format=payload.file_format,
        status="completed",
        generated_by=user.id,
        generated_at=datetime.now(timezone.utc),
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return _to_dict(report)


@router.delete("/{report_id}")
async def delete_report(
    report_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from uuid import UUID
    report = db.query(Report).filter(Report.id == UUID(report_id)).first()
    if not report:
        raise HTTPException(status_code=404, detail="Rapport introuvable")
    assert_same_organization(user, report.organization_id)
    db.delete(report)
    db.commit()
    return {"ok": True}
