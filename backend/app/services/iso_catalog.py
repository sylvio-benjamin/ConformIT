"""Catalogue ISO Niveau A — métadonnées officielles uniquement, pas le texte des normes.

Source : ISO Open Data `iso_deliverables_metadata` (ODC-By 1.0).
Aucun téléchargement de PDF. Aucune API inventée.
"""

from __future__ import annotations

import csv
import io
import json
import re
from datetime import date, datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple

OFFICIAL_PORTAL = "https://www.iso.org/open-data.html"
OFFICIAL_CSV = (
    "https://isopublicstorageprod.blob.core.windows.net/opendata/"
    "_latest/iso_deliverables_metadata/csv/iso_deliverables_metadata.csv"
)
DATASET_ID = "iso_deliverables_metadata"
LICENSE = "ODC-By-1.0"

# Stages harmonisés (ponctuation omise) : 90.99 / 95.99 = withdrawal.
WITHDRAWN_STAGES = frozenset({9099, 9599})

_ISO_NUMBER = re.compile(r"ISO(?:/IEC|/ASTM|/IEEE)?\s+(\d+)", re.IGNORECASE)


def is_withdrawn(current_stage: Optional[int]) -> bool:
    if current_stage is None:
        return False
    if current_stage in WITHDRAWN_STAGES:
        return True
    return current_stage >= 9500


def framework_code_from_reference(reference: str) -> Optional[str]:
    """Lie une référence catalogue (ISO 27001:2022) au framework_code existant (iso27001)."""
    if not reference:
        return None
    match = _ISO_NUMBER.search(reference)
    if not match:
        return None
    return f"iso{match.group(1)}"


def _parse_list(raw: Any) -> List[Any]:
    if raw is None or raw == "":
        return []
    if isinstance(raw, list):
        return raw
    text = str(raw).strip()
    if not text:
        return []
    try:
        parsed = json.loads(text.replace("'", '"'))
        return parsed if isinstance(parsed, list) else [parsed]
    except json.JSONDecodeError:
        return [item.strip() for item in text.strip("[]").split(",") if item.strip()]


def _parse_int(raw: Any) -> Optional[int]:
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _parse_date(raw: Any) -> Optional[date]:
    if not raw:
        return None
    text = str(raw).strip()
    if not text:
        return None
    try:
        return datetime.strptime(text[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def normalize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """Normalise une ligne CSV/JSON officielle. Champs sans source = omis."""
    iso_id = _parse_int(row.get("id"))
    if iso_id is None:
        raise ValueError("id ISO manquant ou invalide")
    reference = (row.get("reference") or "").strip()
    if not reference:
        raise ValueError(f"reference manquante pour id={iso_id}")
    stage = _parse_int(row.get("currentStage") or row.get("current_stage"))
    title_en = row.get("title.en") or row.get("title_en")
    if isinstance(row.get("title"), dict):
        title_en = title_en or row["title"].get("en")
        title_fr = row["title"].get("fr")
    else:
        title_fr = row.get("title.fr") or row.get("title_fr")
    return {
        "iso_id": iso_id,
        "reference": reference,
        "title_en": (title_en or "")[:2000] or None,
        "title_fr": (title_fr or "")[:2000] or None,
        "deliverable_type": (row.get("deliverableType") or row.get("deliverable_type") or "")[:20] or None,
        "supplement_type": (row.get("supplementType") or row.get("supplement_type") or "")[:20] or None,
        "edition": _parse_int(row.get("edition")),
        "publication_date": _parse_date(row.get("publicationDate") or row.get("publication_date")),
        "ics_codes": _parse_list(row.get("icsCode") or row.get("ics_codes")),
        "owner_committee": (row.get("ownerCommittee") or row.get("owner_committee") or "")[:120] or None,
        "current_stage": stage,
        "replaces": _parse_list(row.get("replaces")),
        "replaced_by": _parse_list(row.get("replacedBy") or row.get("replaced_by")),
        "languages": _parse_list(row.get("languages")),
        "pages_en": _parse_int(row.get("pages.en") or row.get("pages_en")),
        # Résumé Open Data uniquement — jamais une exigence / RULE-* (Niveau C bloqué).
        "scope_en": row.get("scope.en") or row.get("scope_en"),
        "withdrawn": is_withdrawn(stage),
        "framework_code": framework_code_from_reference(reference),
        "metadata_source": DATASET_ID,
        "official_source": OFFICIAL_PORTAL,
    }


def parse_official_csv(text: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    reader = csv.DictReader(io.StringIO(text))
    items: List[Dict[str, Any]] = []
    errors: List[str] = []
    for index, row in enumerate(reader, start=2):
        try:
            items.append(normalize_row(row))
        except ValueError as exc:
            errors.append(f"ligne {index}: {exc}")
    return items, errors


def upsert_records(store: Dict[int, Dict[str, Any]], records: Iterable[Dict[str, Any]]) -> Tuple[int, int]:
    """Upsert idempotent par iso_id. Retourne (inserted, updated)."""
    inserted = updated = 0
    for record in records:
        key = record["iso_id"]
        if key in store:
            store[key] = record
            updated += 1
        else:
            store[key] = record
            inserted += 1
    return inserted, updated


def catalog_stats(store: Dict[int, Dict[str, Any]]) -> Dict[str, int]:
    withdrawn = sum(1 for item in store.values() if item.get("withdrawn"))
    return {
        "total": len(store),
        "withdrawn": withdrawn,
        "current": len(store) - withdrawn,
    }


def select_applicable_deliverables(
    catalog: Iterable[Dict[str, Any]],
    decisions: Iterable[Dict[str, Any]],
    *,
    include_withdrawn: bool = False,
) -> List[Dict[str, Any]]:
    """Petit ensemble pertinent : frameworks applicables × catalogue, hors normes retirées."""
    codes = {
        item["framework_code"]
        for item in decisions
        if item.get("applicable") and item.get("framework_code")
    }
    selected: List[Dict[str, Any]] = []
    for record in catalog:
        if record.get("framework_code") not in codes:
            continue
        if record.get("withdrawn") and not include_withdrawn:
            continue
        selected.append(record)
    return selected


def persist_records(session, records: Iterable[Dict[str, Any]]) -> Tuple[int, int]:
    """Upsert SQLAlchemy par iso_id officiel. Idempotent."""
    from app.models.iso_catalog import IsoDeliverable

    inserted = updated = 0
    for record in records:
        row = session.query(IsoDeliverable).filter(
            IsoDeliverable.iso_id == record["iso_id"]
        ).first()
        if row is None:
            session.add(IsoDeliverable(**record))
            inserted += 1
        else:
            for key, value in record.items():
                setattr(row, key, value)
            updated += 1
    session.commit()
    return inserted, updated
