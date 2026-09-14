"""API incidents, isolée par organisation."""

from typing import Optional
from uuid import UUID as PyUUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.permissions import assert_same_organization, get_current_user
from app.database import get_db
from app.models.incidents import Incident
from app.models.organizations import User
from app.schemas.incidents import IncidentCreate, IncidentUpdate

router = APIRouter(prefix="/api/incidents", tags=["incidents"])

_STATUS_MAP = {
    "open": "reported",
    "reported": "reported",
    "investigating": "investigating",
    "resolved": "resolved",
    "closed": "closed",
}


def _code(db: Session, organization_id: PyUUID) -> str:
    count = db.query(Incident).filter(Incident.organization_id == organization_id).count()
    return f"INC-{count + 1:03d}"


def _to_dict(incident: Incident) -> dict:
    return {
        "id": str(incident.id),
        "code": incident.code,
        "title": incident.title,
        "name": incident.title,
        "description": incident.description,
        "incident_type": incident.incident_type,
        "severity": incident.severity,
        "status": incident.status,
        "reported_by": str(incident.reported_by) if incident.reported_by else None,
        "reported_at": incident.reported_at.isoformat() if incident.reported_at else None,
        "date": incident.reported_at.isoformat() if incident.reported_at else None,
        "impact_description": incident.impact_description,
        "created_at": incident.created_at.isoformat() if incident.created_at else None,
        "updated_at": incident.updated_at.isoformat() if incident.updated_at else None,
    }


@router.get("")
async def list_incidents(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    status: Optional[str] = Query(None),
):
    query = db.query(Incident)
    if not user.is_platform_admin:
        query = query.filter(Incident.organization_id == user.organization_id)
    if status:
        query = query.filter(Incident.status == _STATUS_MAP.get(status, status))
    return {"incidents": [_to_dict(i) for i in query.order_by(Incident.created_at.desc()).all()]}


@router.get("/{incident_id}")
async def get_incident(
    incident_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    incident = db.query(Incident).filter(Incident.id == PyUUID(incident_id)).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident introuvable")
    assert_same_organization(user, incident.organization_id)
    return _to_dict(incident)


@router.post("", status_code=201)
async def create_incident(
    payload: IncidentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user.organization_id:
        raise HTTPException(status_code=400, detail="Aucune organisation associée")
    incident = Incident(
        organization_id=user.organization_id,
        code=_code(db, user.organization_id),
        title=payload.title,
        description=payload.description,
        incident_type=payload.incident_type,
        severity=payload.severity or "medium",
        status="reported",
        reported_by=user.id,
        impact_description=payload.impact_description,
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return _to_dict(incident)


@router.put("/{incident_id}")
async def update_incident(
    incident_id: str,
    payload: IncidentUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    incident = db.query(Incident).filter(Incident.id == PyUUID(incident_id)).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident introuvable")
    assert_same_organization(user, incident.organization_id)
    data = payload.model_dump(exclude_unset=True)
    if "status" in data and data["status"] in _STATUS_MAP:
        data["status"] = _STATUS_MAP[data["status"]]
    for key, value in data.items():
        setattr(incident, key, value)
    db.commit()
    db.refresh(incident)
    return _to_dict(incident)


@router.delete("/{incident_id}")
async def delete_incident(
    incident_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    incident = db.query(Incident).filter(Incident.id == PyUUID(incident_id)).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident introuvable")
    assert_same_organization(user, incident.organization_id)
    db.delete(incident)
    db.commit()
    return {"ok": True}
