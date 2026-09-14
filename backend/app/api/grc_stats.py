"""Agrégats GRC pour le dashboard."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.permissions import get_current_user
from app.database import get_db
from app.models.controls import Control
from app.models.incidents import Incident
from app.models.kris import KRI
from app.models.organizations import User
from app.models.reports import Report
from app.models.risks import Risk

router = APIRouter(prefix="/api/grc", tags=["grc"])


@router.get("/stats")
async def grc_stats(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    org_id = user.organization_id
    if not org_id and not user.is_platform_admin:
        return {
            "totalRisks": 0,
            "criticalRisks": 0,
            "totalControls": 0,
            "activeControls": 0,
            "totalKRIs": 0,
            "activeKRIs": 0,
            "totalIncidents": 0,
            "openIncidents": 0,
            "complianceScore": 0,
            "totalReports": 0,
        }

    def scoped(model):
        query = db.query(model)
        if not user.is_platform_admin:
            query = query.filter(model.organization_id == org_id)
        return query

    risks = scoped(Risk).all()
    controls = scoped(Control).all()
    kris = scoped(KRI).all()
    incidents = scoped(Incident).all()
    reports = scoped(Report).all()

    return {
        "totalRisks": len(risks),
        "criticalRisks": sum(1 for r in risks if (r.priority or "").lower() == "critical"),
        "totalControls": len(controls),
        "activeControls": sum(1 for c in controls if c.status in ("in_progress", "completed", "verified")),
        "totalKRIs": len(kris),
        "activeKRIs": sum(1 for k in kris if k.is_active),
        "totalIncidents": len(incidents),
        "openIncidents": sum(1 for i in incidents if i.status in ("reported", "investigating")),
        "complianceScore": 0,
        "totalReports": len(reports),
    }
