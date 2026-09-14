"""API KRIs, isolée par organisation."""

from typing import Optional
from uuid import UUID as PyUUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.permissions import assert_same_organization, get_current_user
from app.database import get_db
from app.models.kris import KRI
from app.models.organizations import User
from app.schemas.kris import KRICreate, KRIUpdate

router = APIRouter(prefix="/api/kris", tags=["kris"])


def _code(db: Session, organization_id: PyUUID) -> str:
    count = db.query(KRI).filter(KRI.organization_id == organization_id).count()
    return f"KRI-{count + 1:03d}"


def _to_dict(kri: KRI) -> dict:
    return {
        "id": str(kri.id),
        "code": kri.code,
        "name": kri.name,
        "description": kri.description,
        "risk_id": str(kri.risk_id) if kri.risk_id else None,
        "unit": kri.unit,
        "frequency": kri.frequency,
        "is_active": kri.is_active,
        "status": "active" if kri.is_active else "inactive",
        "threshold": float(kri.calculation_formula) if False else None,
        "created_at": kri.created_at.isoformat() if kri.created_at else None,
        "updated_at": kri.updated_at.isoformat() if kri.updated_at else None,
    }


@router.get("")
async def list_kris(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(KRI)
    if not user.is_platform_admin:
        query = query.filter(KRI.organization_id == user.organization_id)
    return {"kris": [_to_dict(k) for k in query.order_by(KRI.created_at.desc()).all()]}


@router.get("/{kri_id}")
async def get_kri(
    kri_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    kri = db.query(KRI).filter(KRI.id == PyUUID(kri_id)).first()
    if not kri:
        raise HTTPException(status_code=404, detail="KRI introuvable")
    assert_same_organization(user, kri.organization_id)
    return _to_dict(kri)


@router.post("", status_code=201)
async def create_kri(
    payload: KRICreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user.organization_id:
        raise HTTPException(status_code=400, detail="Aucune organisation associée")
    kri = KRI(
        organization_id=user.organization_id,
        code=_code(db, user.organization_id),
        name=payload.name,
        description=payload.description,
        data_source=payload.data_source or "manual",
        unit=payload.unit,
        frequency=payload.frequency or "monthly",
        owner_id=user.id,
        is_active=True,
    )
    db.add(kri)
    db.commit()
    db.refresh(kri)
    return _to_dict(kri)


@router.put("/{kri_id}")
async def update_kri(
    kri_id: str,
    payload: KRIUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    kri = db.query(KRI).filter(KRI.id == PyUUID(kri_id)).first()
    if not kri:
        raise HTTPException(status_code=404, detail="KRI introuvable")
    assert_same_organization(user, kri.organization_id)
    data = payload.model_dump(exclude_unset=True)
    if "owner_id" in data and data["owner_id"]:
        data["owner_id"] = PyUUID(data["owner_id"])
    for key, value in data.items():
        if key.startswith("threshold_"):
            continue
        setattr(kri, key, value)
    db.commit()
    db.refresh(kri)
    return _to_dict(kri)


@router.delete("/{kri_id}")
async def delete_kri(
    kri_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    kri = db.query(KRI).filter(KRI.id == PyUUID(kri_id)).first()
    if not kri:
        raise HTTPException(status_code=404, detail="KRI introuvable")
    assert_same_organization(user, kri.organization_id)
    db.delete(kri)
    db.commit()
    return {"ok": True}
