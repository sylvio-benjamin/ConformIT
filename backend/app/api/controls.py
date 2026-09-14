"""API contrôles, isolée par organisation."""

from typing import Optional
from uuid import UUID as PyUUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.permissions import assert_same_organization, get_current_user
from app.database import get_db
from app.models.controls import Control
from app.models.organizations import User
from app.schemas.controls import ControlCreate, ControlUpdate

router = APIRouter(prefix="/api/controls", tags=["controls"])


def _code(db: Session, organization_id: PyUUID) -> str:
    count = db.query(Control).filter(Control.organization_id == organization_id).count()
    return f"CTL-{count + 1:03d}"


def _to_dict(control: Control) -> dict:
    return {
        "id": str(control.id),
        "code": control.code,
        "name": control.name,
        "description": control.description,
        "control_type": control.control_type,
        "type": control.control_type,
        "control_category": control.control_category,
        "owner_id": str(control.owner_id) if control.owner_id else None,
        "status": control.status,
        "effectiveness_rating": control.effectiveness_rating,
        "documentation_url": control.documentation_url,
        "created_at": control.created_at.isoformat() if control.created_at else None,
        "updated_at": control.updated_at.isoformat() if control.updated_at else None,
    }


@router.get("")
async def list_controls(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    status: Optional[str] = Query(None),
):
    query = db.query(Control)
    if not user.is_platform_admin:
        query = query.filter(Control.organization_id == user.organization_id)
    if status:
        query = query.filter(Control.status == status)
    return {"controls": [_to_dict(c) for c in query.order_by(Control.created_at.desc()).all()]}


@router.get("/{control_id}")
async def get_control(
    control_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    control = db.query(Control).filter(Control.id == PyUUID(control_id)).first()
    if not control:
        raise HTTPException(status_code=404, detail="Contrôle introuvable")
    assert_same_organization(user, control.organization_id)
    return _to_dict(control)


@router.post("", status_code=201)
async def create_control(
    payload: ControlCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user.organization_id:
        raise HTTPException(status_code=400, detail="Aucune organisation associée")
    control = Control(
        organization_id=user.organization_id,
        code=_code(db, user.organization_id),
        name=payload.name,
        description=payload.description,
        control_type=payload.control_type,
        control_category=payload.control_category,
        owner_id=user.id,
        status="in_progress",
        documentation_url=payload.documentation_url,
    )
    db.add(control)
    db.commit()
    db.refresh(control)
    return _to_dict(control)


@router.put("/{control_id}")
async def update_control(
    control_id: str,
    payload: ControlUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    control = db.query(Control).filter(Control.id == PyUUID(control_id)).first()
    if not control:
        raise HTTPException(status_code=404, detail="Contrôle introuvable")
    assert_same_organization(user, control.organization_id)
    data = payload.model_dump(exclude_unset=True)
    if "owner_id" in data and data["owner_id"]:
        data["owner_id"] = PyUUID(data["owner_id"])
    for key, value in data.items():
        setattr(control, key, value)
    db.commit()
    db.refresh(control)
    return _to_dict(control)


@router.delete("/{control_id}")
async def delete_control(
    control_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    control = db.query(Control).filter(Control.id == PyUUID(control_id)).first()
    if not control:
        raise HTTPException(status_code=404, detail="Contrôle introuvable")
    assert_same_organization(user, control.organization_id)
    db.delete(control)
    db.commit()
    return {"ok": True}
