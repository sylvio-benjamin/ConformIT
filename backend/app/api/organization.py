"""Profil d'organisation, applicabilité et catalogue KB (contrôles globaux)."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.permissions import get_current_user
from app.database import get_db
from app.models.applicability import (
    ApplicabilityDecision,
    ApplicabilityRule,
    KbControl,
    OrganizationProfile,
)
from app.models.iso_catalog import IsoDeliverable
from app.models.organizations import Organization, User
from app.services.applicability import (
    DEFAULT_KB_CONTROLS,
    DEFAULT_RULES,
    evaluate_profile,
    evaluate_profile_detailed,
    profile_to_dict,
)
from app.evaluation_layers import evaluation_contract, explain_layers
from app.services.iso_catalog import LICENSE as ISO_ODC_LICENSE
from app.services.iso_catalog import OFFICIAL_PORTAL

router = APIRouter(prefix="/api/v1/organizations/me", tags=["organizations"])
kb_router = APIRouter(prefix="/api/v1/kb", tags=["knowledge-base"])


class ProfilePayload(BaseModel):
    sector: Optional[str] = None
    size: Optional[str] = None
    country: Optional[str] = Field(default="FR", max_length=2)
    criticality: Optional[str] = "medium"
    processes_personal_data: bool = False
    hosting: Optional[str] = "cloud"
    listed_company: bool = False
    notes: Optional[str] = None


def _org(db: Session, user: User) -> Organization:
    if not user.organization_id:
        raise HTTPException(status_code=400, detail="Aucune organisation associée")
    org = db.query(Organization).filter(Organization.id == user.organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organisation introuvable")
    return org


def _ensure_defaults(db: Session) -> None:
    if db.query(ApplicabilityRule).count() == 0:
        for rule in DEFAULT_RULES:
            db.add(ApplicabilityRule(
                code=rule["code"],
                framework_code=rule["framework_code"],
                condition=rule["condition"],
                reason=rule["reason"],
                is_active=True,
            ))
    if db.query(KbControl).count() == 0:
        for item in DEFAULT_KB_CONTROLS:
            db.add(KbControl(**item, is_active=True))
    db.commit()


def _active_rules(db: Session) -> List[dict]:
    _ensure_defaults(db)
    rows = db.query(ApplicabilityRule).filter(ApplicabilityRule.is_active.is_(True)).all()
    if not rows:
        return DEFAULT_RULES
    return [
        {
            "code": row.code,
            "framework_code": row.framework_code,
            "condition": row.condition or {},
            "reason": row.reason,
        }
        for row in rows
    ]


def _persist_decisions(db: Session, organization_id, evaluations: List[dict]) -> List[dict]:
    stored = []
    for item in evaluations:
        row = (
            db.query(ApplicabilityDecision)
            .filter(
                ApplicabilityDecision.organization_id == organization_id,
                ApplicabilityDecision.framework_code == item["framework_code"],
            )
            .first()
        )
        if row and row.override:
            stored.append({
                "framework_code": row.framework_code,
                "applicable": row.applicable,
                "reason": row.reason,
                "confidence": row.confidence,
                "source_rule": row.source_rule,
                "override": True,
            })
            continue
        if not row:
            row = ApplicabilityDecision(
                organization_id=organization_id,
                framework_code=item["framework_code"],
            )
            db.add(row)
        row.applicable = item["applicable"]
        row.reason = item["reason"]
        row.confidence = item["confidence"]
        row.source_rule = item["source_rule"]
        row.override = False
        stored.append({**item, "override": False})
    db.commit()
    return stored


@router.get("/profile")
async def get_profile(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    org = _org(db, user)
    row = db.query(OrganizationProfile).filter(
        OrganizationProfile.organization_id == org.id
    ).first()
    return {"organization_id": str(org.id), "name": org.name, **profile_to_dict(row)}


@router.put("/profile")
async def put_profile(
    payload: ProfilePayload,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    org = _org(db, user)
    row = db.query(OrganizationProfile).filter(
        OrganizationProfile.organization_id == org.id
    ).first()
    if not row:
        row = OrganizationProfile(organization_id=org.id)
        db.add(row)
    row.sector = payload.sector
    row.size = payload.size
    row.country = (payload.country or "FR").upper()
    row.criticality = payload.criticality
    row.processes_personal_data = payload.processes_personal_data
    row.hosting = payload.hosting
    row.listed_company = payload.listed_company
    row.notes = payload.notes
    db.commit()
    db.refresh(row)

    decisions = _persist_decisions(
        db,
        org.id,
        evaluate_profile(profile_to_dict(row), _active_rules(db)),
    )
    return {"profile": profile_to_dict(row), "applicability": decisions}


@router.get("/applicability")
async def get_applicability(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    org = _org(db, user)
    rows = db.query(ApplicabilityDecision).filter(
        ApplicabilityDecision.organization_id == org.id
    ).all()
    if not rows:
        profile = db.query(OrganizationProfile).filter(
            OrganizationProfile.organization_id == org.id
        ).first()
        return {
            "decisions": evaluate_profile(profile_to_dict(profile), _active_rules(db))
        }
    return {
        "decisions": [
            {
                "framework_code": row.framework_code,
                "applicable": row.applicable,
                "reason": row.reason,
                "confidence": row.confidence,
                "source_rule": row.source_rule,
                "override": row.override,
            }
            for row in rows
        ]
    }


@router.post("/applicability/evaluate")
async def evaluate_applicability(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    org = _org(db, user)
    profile = db.query(OrganizationProfile).filter(
        OrganizationProfile.organization_id == org.id
    ).first()
    decisions = _persist_decisions(
        db,
        org.id,
        evaluate_profile(profile_to_dict(profile), _active_rules(db)),
    )
    return {"decisions": decisions}


@router.get("/applicable-standards")
async def list_applicable_standards(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Niveau B → A : normes catalogue liées aux frameworks applicables de CETTE orga."""
    org = _org(db, user)
    profile = db.query(OrganizationProfile).filter(
        OrganizationProfile.organization_id == org.id
    ).first()
    decisions = evaluate_profile_detailed(profile_to_dict(profile), _active_rules(db))
    codes = [item["framework_code"] for item in decisions if item["applicable"]]
    if codes:
        rows = (
            db.query(IsoDeliverable)
            .filter(
                IsoDeliverable.withdrawn.is_(False),
                IsoDeliverable.framework_code.in_(codes),
            )
            .order_by(IsoDeliverable.reference)
            .limit(200)
            .all()
        )
    else:
        rows = []
    return {
        "organization_id": str(org.id),
        "decisions": decisions,
        "standards": [_deliverable_public(row) for row in rows],
        "level": "A",
        "license": ISO_ODC_LICENSE,
        "official_source": OFFICIAL_PORTAL,
        "note": "Métadonnées catalogue uniquement. Pas le texte des normes. scope.en n'est pas une exigence.",
        "evaluation": evaluation_contract(decisions),
        "applicability_explained": explain_layers(decisions),
    }


def _deliverable_public(row: IsoDeliverable) -> dict:
    return {
        "iso_id": row.iso_id,
        "reference": row.reference,
        "title_en": row.title_en,
        "title_fr": row.title_fr,
        "edition": row.edition,
        "publication_date": row.publication_date.isoformat() if row.publication_date else None,
        "ics_codes": row.ics_codes or [],
        "owner_committee": row.owner_committee,
        "current_stage": row.current_stage,
        "withdrawn": row.withdrawn,
        "framework_code": row.framework_code,
        "official_source": row.official_source,
        "metadata_source": row.metadata_source,
    }


@kb_router.get("/controls")
async def list_kb_controls(
    framework: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _ = user
    _ensure_defaults(db)
    query = db.query(KbControl).filter(KbControl.is_active.is_(True))
    if framework:
        query = query.filter(KbControl.framework_code == framework)
    return {
        "controls": [
            {
                "id": str(row.id),
                "code": row.code,
                "title": row.title,
                "description": row.description,
                "framework_code": row.framework_code,
                "control_type": row.control_type,
            }
            for row in query.order_by(KbControl.code).all()
        ]
    }


@kb_router.get("/iso-standards")
async def list_iso_standards(
    q: Optional[str] = None,
    withdrawn: Optional[bool] = False,
    framework: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Catalogue global Niveau A. JWT requis. Aucune donnée d'organisation."""
    _ = user
    capped = max(1, min(limit, 200))
    query = db.query(IsoDeliverable)
    if withdrawn is False:
        query = query.filter(IsoDeliverable.withdrawn.is_(False))
    elif withdrawn is True:
        query = query.filter(IsoDeliverable.withdrawn.is_(True))
    if framework:
        query = query.filter(IsoDeliverable.framework_code == framework)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(
            or_(
                IsoDeliverable.reference.ilike(like),
                IsoDeliverable.title_en.ilike(like),
            )
        )
    rows = query.order_by(IsoDeliverable.reference).limit(capped).all()
    return {
        "standards": [_deliverable_public(row) for row in rows],
        "count": len(rows),
        "level": "A",
        "license": ISO_ODC_LICENSE,
        "official_source": OFFICIAL_PORTAL,
        "note": "Métadonnées ISO Open Data (ODC-By 1.0). Pas le texte des normes.",
    }
