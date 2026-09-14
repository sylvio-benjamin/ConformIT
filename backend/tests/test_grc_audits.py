from app.services.grc_audits import AUDIT_TYPES, FINDING_SEVERITIES, FINDING_STATUSES, audit_to_dict


def test_audit_vocabularies():
    assert "internal" in AUDIT_TYPES
    assert "external" in AUDIT_TYPES
    assert FINDING_STATUSES == {"open", "in_progress", "closed"}
    assert "critical" in FINDING_SEVERITIES


class _Audit:
    id = "11111111-1111-1111-1111-111111111111"
    title = "Audit interne"
    audit_type = "internal"
    framework_code = "iso31000"
    status = "planned"
    scope = None
    auditor_name = None
    started_at = None
    finished_at = None
    created_at = None


def test_audit_to_dict_without_findings():
    payload = audit_to_dict(_Audit())
    assert payload["title"] == "Audit interne"
    assert "findings" not in payload
