"""Catalogue ISO Niveau A + applicabilité explicable. Sans import de app.main."""

from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.models.applicability import ApplicabilityDecision
from app.models.iso_catalog import IsoDeliverable
from app.services.applicability import evaluate_profile, evaluate_profile_detailed
from app.evaluation_layers import (
    ARCHITECTURE_RULE,
    EVOLUTION_RULE,
    PUBLIC_CATALOG_FIELDS,
    SCOPE_EN_FORBIDDEN,
    evaluation_contract,
    public_deliverable,
    refuse_scope_as_normative,
)
from app.services.iso_catalog import (
    framework_code_from_reference,
    is_withdrawn,
    normalize_row,
    parse_official_csv,
    select_applicable_deliverables,
    upsert_records,
)

FIXTURE = Path(__file__).parent / "fixtures" / "iso_deliverables_sample.csv"


def test_valid_import_from_official_columns():
    items, errors = parse_official_csv(FIXTURE.read_text(encoding="utf-8"))
    assert errors == []
    assert len(items) == 3
    by_id = {row["iso_id"]: row for row in items}
    assert by_id[100001]["reference"] == "ISO/IEC 27001:2022"
    assert by_id[100001]["framework_code"] == "iso27001"
    assert by_id[100001]["withdrawn"] is False
    assert by_id[100001]["owner_committee"] == "ISO/IEC JTC 1/SC 27"
    assert by_id[100001]["ics_codes"] == ["35.030"]


def test_upsert_duplicate_then_update():
    items, _ = parse_official_csv(FIXTURE.read_text(encoding="utf-8"))
    store = {}
    inserted, updated = upsert_records(store, items)
    assert inserted == 3 and updated == 0
    again_inserted, again_updated = upsert_records(store, items)
    assert again_inserted == 0 and again_updated == 3
    changed = {**items[0], "title_en": "Updated title"}
    upsert_records(store, [changed])
    assert store[100001]["title_en"] == "Updated title"


def test_withdrawn_stage():
    assert is_withdrawn(6060) is False
    assert is_withdrawn(9599) is True
    assert is_withdrawn(9099) is True
    items, _ = parse_official_csv(FIXTURE.read_text(encoding="utf-8"))
    withdrawn = next(item for item in items if item["iso_id"] == 100003)
    assert withdrawn["withdrawn"] is True
    assert withdrawn["replaced_by"] == [100001]


def test_invalid_rows_are_reported():
    raw = (
        "id,reference,currentStage\n"
        ",ISO 1,6060\n"
        "12,,6060\n"
        "13,ISO 9001:2015,6060\n"
    )
    items, errors = parse_official_csv(raw)
    assert len(items) == 1
    assert len(errors) == 2
    assert items[0]["iso_id"] == 13


def test_framework_code_from_reference():
    assert framework_code_from_reference("ISO/IEC 27001:2022") == "iso27001"
    assert framework_code_from_reference("ISO 31000:2018") == "iso31000"
    assert framework_code_from_reference("IWA 42") is None


def test_normalize_rejects_missing_id():
    try:
        normalize_row({"reference": "ISO 1"})
    except ValueError as exc:
        assert "id ISO" in str(exc)
    else:
        raise AssertionError("attendu ValueError")


def test_applicability_empty_profile_explains_negatives():
    detailed = evaluate_profile_detailed({})
    rgpd = next(item for item in detailed if item["framework_code"] == "rgpd")
    assert rgpd["applicable"] is False
    assert rgpd["reasons"] == ["Aucun critère d'applicabilité détecté"]
    iso = next(item for item in detailed if item["framework_code"] == "iso31000")
    assert iso["applicable"] is True
    assert "Socle de gestion des risques" in iso["reasons"][0]


def test_applicability_multiple_criteria_all_reasons():
    detailed = evaluate_profile_detailed({
        "criticality": "high",
        "hosting": "cloud",
    })
    iso27005 = next(item for item in detailed if item["framework_code"] == "iso27005")
    assert iso27005["applicable"] is True
    assert len(iso27005["reasons"]) == 2
    assert len(iso27005["source_rules"]) == 2


def test_applicable_and_not_applicable_standards():
    items, _ = parse_official_csv(FIXTURE.read_text(encoding="utf-8"))
    decisions = [
        {"framework_code": "iso27001", "applicable": True},
        {"framework_code": "iso9001", "applicable": False},
    ]
    selected = select_applicable_deliverables(items, decisions)
    assert [row["iso_id"] for row in selected] == [100001]


def test_withdrawn_excluded_from_engine_set():
    items, _ = parse_official_csv(FIXTURE.read_text(encoding="utf-8"))
    decisions = [{"framework_code": "iso99999", "applicable": True}]
    assert select_applicable_deliverables(items, decisions) == []


def test_org_a_profile_not_equal_org_b():
    org_a = evaluate_profile({
        "country": "FR",
        "processes_personal_data": True,
        "listed_company": False,
    })
    org_b = evaluate_profile({
        "country": "US",
        "processes_personal_data": False,
        "listed_company": True,
    })
    rgpd_a = next(item for item in org_a if item["framework_code"] == "rgpd")
    rgpd_b = next(item for item in org_b if item["framework_code"] == "rgpd")
    sox_a = next(item for item in org_a if item["framework_code"] == "sox")
    sox_b = next(item for item in org_b if item["framework_code"] == "sox")
    assert rgpd_a["applicable"] is True
    assert rgpd_b["applicable"] is False
    assert sox_a["applicable"] is False
    assert sox_b["applicable"] is True


def test_catalog_is_global_decisions_are_org_scoped():
    assert "organization_id" not in IsoDeliverable.__table__.c
    assert "organization_id" in ApplicabilityDecision.__table__.c
    org_a, org_b = uuid4(), uuid4()
    assert org_a != org_b


def test_scope_en_is_never_a_rule():
    assert "scope_en" not in PUBLIC_CATALOG_FIELDS
    payload = public_deliverable({
        "iso_id": 1,
        "reference": "ISO/IEC 27001:2022",
        "scope_en": "This document specifies requirements…",
        "title_en": "ISMS",
    })
    assert "scope_en" not in payload
    try:
        refuse_scope_as_normative("This document specifies requirements…")
    except ValueError as exc:
        assert "pas un contenu normatif" in str(exc)
    else:
        raise AssertionError("scope.en ne doit pas devenir une exigence")


def test_evaluation_contract_does_not_score():
    contract = evaluation_contract([
        {"framework_code": "iso27005", "applicable": True, "reasons": ["cloud"]},
        {"framework_code": "sox", "applicable": False},
    ])
    assert contract["catalog_computes_score"] is False
    assert contract["applicability_computes_risk"] is False
    assert contract["scope_en_is_normative"] is False
    assert contract["level_c_status"] == "BLOCKED_LICENSE"
    assert contract["scoring_is_referential_agnostic"] is True
    assert contract["level_c_is_new_rule_source"] is True
    assert contract["architecture_rule"] == ARCHITECTURE_RULE
    assert contract["evolution_rule"] == EVOLUTION_RULE
    assert contract["separation_rule"] == "Extraire ≠ évaluer ≠ scorer."
    assert contract["llm_is_semantic_authority"] is False
    assert contract["unknown_is_error"] is False
    assert contract["boundaries"]["question"] == "interprète les faits via une condition"
    assert SCOPE_EN_FORBIDDEN == {"question", "exigence", "rule", "finding", "score"}
    assert contract["applicable_frameworks"] == ["iso27005"]


def test_iso_catalog_endpoints_require_auth():
    from app.api.organization import kb_router, router
    from app.database import get_db

    app = FastAPI()
    app.include_router(router)
    app.include_router(kb_router)

    def _no_db():
        yield None

    app.dependency_overrides[get_db] = _no_db
    client = TestClient(app)
    assert client.get("/api/v1/kb/iso-standards").status_code == 401
    assert client.get("/api/v1/organizations/me/applicable-standards").status_code == 401
