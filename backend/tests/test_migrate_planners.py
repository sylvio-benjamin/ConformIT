"""Planificateurs du script de migration (sans accès Neon)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.migrate_firebase import (  # noqa: E402
    _map_priority,
    plan_grc_controls,
    plan_grc_incidents,
    plan_grc_risks,
    plan_users,
    uid_email_map,
)


SAMPLE = {
    "utilisateurs": {
        "uid1": {"email": "a@example.com", "nom": "A", "admin": True},
        "uid2": {"nom": "Sans email"},
    },
    "grc": {
        "uid1": {
            "risks": {"r1": {"name": "Fraude", "severity": "high"}},
            "controls": {"c1": {"name": "Revue", "type": "preventive"}},
            "incidents": {"i1": {"title": "Fuite", "severity": "critical"}},
        }
    },
}


def test_plan_users_skips_missing_email():
    planned = plan_users(SAMPLE)
    assert any(item["status"] == "ok" and item["email"] == "a@example.com" for item in planned)
    assert any(item["status"] == "skip" for item in planned)


def test_plan_grc_entities():
    assert plan_grc_risks(SAMPLE)[0]["title"] == "Fraude"
    assert plan_grc_controls(SAMPLE)[0]["name"] == "Revue"
    assert plan_grc_incidents(SAMPLE)[0]["severity"] == "critical"


def test_priority_aliases():
    assert _map_priority("élevé") == "high"
    assert _map_priority("unknown") is None


def test_legacy_uid_resolves_via_email_not_column():
    mapping = uid_email_map(plan_users(SAMPLE))
    assert mapping["uid1"] == "a@example.com"
    assert "uid2" not in mapping
