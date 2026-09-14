#!/usr/bin/env python3
"""
Outil one-shot archivé — hors runtime.

Import historique Firebase RTDB → Neon. Non importé par FastAPI ni le frontend.
Ne touche plus `users.firebase_uid` (colonne droppée). Rattache users/GRC par email.

Usage:
  python scripts/migrate_firebase.py --source dump.json
  python scripts/migrate_firebase.py --source dump.json --apply
  python scripts/migrate_firebase.py --source dump.json --verify

Par défaut : dry-run. Mots de passe Firebase Auth non migrables.

Suppression définitive (quand la migration historique est close) :
  1. Tous les comptes utiles sont en Neon (inscrits ou importés + mot de passe).
  2. Plus aucun restore RTDB prévu.
  3. Dumps `*rtdb*.json` détruits ou archivés hors git.
  4. Retirer ce script, `tests/test_migrate_planners.py`, et les mentions docs.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))


def load_export(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def plan_users(data: dict) -> list[dict]:
    users = data.get("utilisateurs") or {}
    planned = []
    for uid, raw in users.items():
        if not isinstance(raw, dict):
            continue
        email = (raw.get("email") or "").strip().lower()
        if not email:
            planned.append({"status": "skip", "reason": "email manquant", "uid": uid})
            continue
        planned.append({
            "status": "ok",
            "uid": uid,
            "email": email,
            "nom": raw.get("nom"),
            "prenom": raw.get("prenom"),
            "entreprise": raw.get("entreprise"),
            "telephone": raw.get("telephone"),
            "abonnement": raw.get("abonnement") or "basic",
            "admin": bool(raw.get("admin")),
            "preferences": raw.get("preferences") or {},
        })
    return planned


def plan_grc_risks(data: dict) -> list[dict]:
    grc = data.get("grc") or {}
    rows = []
    for uid, payload in grc.items():
        risks = (payload or {}).get("risks") or {}
        for rid, risk in risks.items():
            if not isinstance(risk, dict):
                continue
            rows.append({
                "uid": uid,
                "legacy_id": rid,
                "title": risk.get("name") or risk.get("title") or "Risque importé",
                "description": risk.get("description"),
                "priority": risk.get("severity") or risk.get("priority"),
                "status": risk.get("status") or "identified",
            })
    return rows


def _map_priority(raw) -> Optional[str]:
    value = str(raw or "").strip().lower()
    aliases = {
        "faible": "low",
        "low": "low",
        "moyen": "medium",
        "medium": "medium",
        "élevé": "high",
        "eleve": "high",
        "high": "high",
        "critique": "critical",
        "critical": "critical",
    }
    return aliases.get(value)


def _map_risk_status(raw) -> str:
    value = str(raw or "").strip().lower()
    if value in {"identified", "assessed", "treated", "accepted", "closed"}:
        return value
    return "identified"


def plan_grc_controls(data: dict) -> list[dict]:
    grc = data.get("grc") or {}
    rows = []
    for uid, payload in grc.items():
        controls = (payload or {}).get("controls") or {}
        for cid, control in controls.items():
            if not isinstance(control, dict):
                continue
            rows.append({
                "uid": uid,
                "legacy_id": cid,
                "name": control.get("name") or control.get("title") or "Contrôle importé",
                "description": control.get("description"),
                "control_type": control.get("type") or control.get("control_type"),
            })
    return rows


def plan_grc_incidents(data: dict) -> list[dict]:
    grc = data.get("grc") or {}
    rows = []
    for uid, payload in grc.items():
        incidents = (payload or {}).get("incidents") or {}
        for iid, incident in incidents.items():
            if not isinstance(incident, dict):
                continue
            rows.append({
                "uid": uid,
                "legacy_id": iid,
                "title": incident.get("title") or incident.get("name") or "Incident importé",
                "description": incident.get("description"),
                "severity": _map_priority(incident.get("severity") or incident.get("priority")),
            })
    return rows


def apply_users(db, planned: list[dict]) -> dict:
    from app.models.organizations import Organization, User

    created = 0
    skipped = 0
    for item in planned:
        if item["status"] != "ok":
            skipped += 1
            continue
        existing = db.query(User).filter(User.email == item["email"]).first()
        if existing:
            skipped += 1
            continue
        org = Organization(
            name=item["entreprise"] or f"Organisation de {item['nom'] or item['email']}",
            plan=item["abonnement"],
        )
        db.add(org)
        db.flush()
        user = User(
            email=item["email"],
            password_hash=None,
            nom=item["nom"],
            prenom=item["prenom"],
            entreprise=item["entreprise"],
            telephone=item["telephone"],
            abonnement=item["abonnement"],
            is_platform_admin=item["admin"],
            preferences=item["preferences"],
            organization_id=org.id,
        )
        db.add(user)
        created += 1
    db.commit()
    return {"created": created, "skipped": skipped}


def uid_email_map(planned_users: list[dict]) -> dict[str, str]:
    return {
        item["uid"]: item["email"]
        for item in planned_users
        if item.get("status") == "ok" and item.get("uid") and item.get("email")
    }


def _user_by_legacy_uid(db, uid: str, uid_emails: dict[str, str]):
    from app.models.organizations import User

    email = uid_emails.get(uid)
    if not email:
        return None
    return db.query(User).filter(User.email == email).first()


def apply_risks(db, planned: list[dict], uid_emails: dict[str, str]) -> dict:
    from app.models.risks import Risk

    created = 0
    skipped = 0
    for index, item in enumerate(planned, start=1):
        user = _user_by_legacy_uid(db, item["uid"], uid_emails)
        if not user or not user.organization_id:
            skipped += 1
            continue
        code = f"IMP-{str(user.organization_id)[:8]}-{index:04d}"
        if db.query(Risk).filter(Risk.code == code).first():
            skipped += 1
            continue
        db.add(Risk(
            organization_id=user.organization_id,
            code=code,
            title=item["title"],
            description=item.get("description"),
            priority=_map_priority(item.get("priority")),
            status=_map_risk_status(item.get("status")),
            created_by=user.id,
            owner_id=user.id,
            meta_data={"legacy_id": item["legacy_id"], "imported_from": "firebase"},
        ))
        created += 1
    db.commit()
    return {"created": created, "skipped": skipped}


def apply_controls(db, planned: list[dict], uid_emails: dict[str, str]) -> dict:
    from app.models.controls import Control

    created = 0
    skipped = 0
    for index, item in enumerate(planned, start=1):
        user = _user_by_legacy_uid(db, item["uid"], uid_emails)
        if not user or not user.organization_id:
            skipped += 1
            continue
        code = f"CTL-IMP-{str(user.organization_id)[:8]}-{index:03d}"
        if db.query(Control).filter(Control.code == code).first():
            skipped += 1
            continue
        db.add(Control(
            organization_id=user.organization_id,
            code=code,
            name=item["name"],
            description=item.get("description"),
            control_type=item.get("control_type"),
            owner_id=user.id,
            status="planned",
        ))
        created += 1
    db.commit()
    return {"created": created, "skipped": skipped}


def apply_incidents(db, planned: list[dict], uid_emails: dict[str, str]) -> dict:
    from app.models.incidents import Incident

    created = 0
    skipped = 0
    for index, item in enumerate(planned, start=1):
        user = _user_by_legacy_uid(db, item["uid"], uid_emails)
        if not user or not user.organization_id:
            skipped += 1
            continue
        code = f"INC-IMP-{str(user.organization_id)[:8]}-{index:03d}"
        if db.query(Incident).filter(Incident.code == code).first():
            skipped += 1
            continue
        db.add(Incident(
            organization_id=user.organization_id,
            code=code,
            title=item["title"],
            description=item.get("description"),
            severity=item.get("severity"),
            status="reported",
            reported_by=user.id,
        ))
        created += 1
    db.commit()
    return {"created": created, "skipped": skipped}


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrer un export RTDB vers PostgreSQL")
    parser.add_argument("--source", required=True, help="Fichier JSON d'export Firebase")
    parser.add_argument("--apply", action="store_true", help="Écrire en base (sinon dry-run)")
    parser.add_argument("--verify", action="store_true", help="Comparer emails export vs users")
    args = parser.parse_args()

    source = Path(args.source)
    if not source.is_absolute():
        source = ROOT / source
    if not source.exists():
        print(f"[ERREUR] Fichier introuvable: {source}")
        return 1

    data = load_export(source)
    users = plan_users(data)
    risks = plan_grc_risks(data)
    controls = plan_grc_controls(data)
    incidents = plan_grc_incidents(data)
    ok_users = [u for u in users if u["status"] == "ok"]
    skipped_users = [u for u in users if u["status"] != "ok"]

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": str(source),
        "dry_run": not args.apply,
        "users_ok": len(ok_users),
        "users_skipped": len(skipped_users),
        "grc_risks": len(risks),
        "grc_controls": len(controls),
        "grc_incidents": len(incidents),
        "skipped_detail": skipped_users,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))

    if args.verify or args.apply:
        from app.database import SessionLocal
        from app.models.organizations import User

        db = SessionLocal()
        try:
            if args.verify:
                emails = {u["email"] for u in ok_users}
                existing = {row.email for row in db.query(User.email).all()}
                print(json.dumps({
                    "in_export_not_in_db": sorted(emails - existing),
                    "in_db_not_in_export": sorted(existing - emails),
                }, indent=2, ensure_ascii=False))
            if args.apply:
                uid_emails = uid_email_map(users)
                stats = {
                    "users": apply_users(db, users),
                    "risks": apply_risks(db, risks, uid_emails),
                    "controls": apply_controls(db, controls, uid_emails),
                    "incidents": apply_incidents(db, incidents, uid_emails),
                }
                print(json.dumps({"applied": stats}, indent=2))
                print("[INFO] Mots de passe non migrés — les users devront passer par /forgot-password.")
        finally:
            db.close()

    log_path = ROOT / "scripts" / "migration_log.json"
    log_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[OK] Journal: {log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
