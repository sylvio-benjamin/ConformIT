"""Snapshot GRC d'organisation (conformité déclarative)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.permissions import get_current_user
from app.database import get_db
from app.models.organizations import Organization, User

router = APIRouter(prefix="/api/v1/organizations/me", tags=["organizations"])

DEFAULT_COMPLIANCE = {
    "iso31000": {"status": "not_assessed", "score": 0},
    "iso27005": {"status": "not_assessed", "score": 0},
    "coso_erm": {"status": "not_assessed", "score": 0},
    "cobit": {"status": "not_assessed", "score": 0},
    "sox": {"status": "not_assessed", "score": 0},
    "rgpd": {"status": "not_assessed", "score": 0},
}


def _org(db: Session, user: User) -> Organization:
    if not user.organization_id:
        raise HTTPException(status_code=400, detail="Aucune organisation associée")
    org = db.query(Organization).filter(Organization.id == user.organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organisation introuvable")
    return org


@router.get("/compliance")
async def get_compliance(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    org = _org(db, user)
    snapshot = org.grc_snapshot or {}
    return snapshot.get("compliance") or DEFAULT_COMPLIANCE


@router.put("/compliance")
async def put_compliance(
    payload: dict,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    org = _org(db, user)
    snapshot = dict(org.grc_snapshot or {})
    snapshot["compliance"] = payload
    org.grc_snapshot = snapshot
    db.commit()
    return snapshot["compliance"]
