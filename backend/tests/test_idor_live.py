"""IDOR contre Neon réel. Ignoré en CI. Lancer : IDOR_LIVE=1 pytest tests/test_idor_live.py"""

from __future__ import annotations

import os
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

pytestmark = pytest.mark.skipif(
    os.getenv("IDOR_LIVE") != "1",
    reason="IDOR_LIVE=1 requis (Neon réel, hors CI)",
)

EMAIL_PREFIX = "idor-p7-"
EMAIL_DOMAIN = "example.test"


def _database_url() -> str:
    import app.config  # charge .env / .env.local

    return (
        os.getenv("DATABASE_URL")
        or os.getenv("POSTGRES_URL")
        or getattr(app.config, "POSTGRES_URL", "")
    )


@pytest.fixture(scope="module")
def live_db():
    url = _database_url()
    if not url or "localhost" in url or "127.0.0.1" in url:
        pytest.skip("DATABASE_URL Neon requis (pas localhost)")

    from app.database import SessionLocal
    from app.models.analyses import Analysis
    from app.models.analysis_jobs import AnalysisFinding, AnalysisJob
    from app.models.compliance_evidence import ComplianceEvidence
    from app.models.grc_audits import AuditFinding, GrcAudit
    from app.models.organizations import Organization, User

    db = SessionLocal()
    created = []

    def _cleanup():
        users = db.query(User).filter(User.email.like(f"{EMAIL_PREFIX}%@{EMAIL_DOMAIN}")).all()
        user_ids = [u.id for u in users]
        org_ids = [u.organization_id for u in users if u.organization_id]
        if user_ids:
            db.query(AuditFinding).filter(AuditFinding.organization_id.in_(org_ids)).delete(synchronize_session=False)
            db.query(GrcAudit).filter(GrcAudit.organization_id.in_(org_ids)).delete(synchronize_session=False)
            db.query(ComplianceEvidence).filter(ComplianceEvidence.organization_id.in_(org_ids)).delete(synchronize_session=False)
            db.query(AnalysisFinding).filter(AnalysisFinding.organization_id.in_(org_ids)).delete(synchronize_session=False)
            db.query(AnalysisJob).filter(AnalysisJob.organization_id.in_(org_ids)).delete(synchronize_session=False)
            db.query(Analysis).filter(Analysis.organization_id.in_(org_ids)).delete(synchronize_session=False)
            db.query(User).filter(User.id.in_(user_ids)).delete(synchronize_session=False)
        if org_ids:
            db.query(Organization).filter(Organization.id.in_(org_ids)).delete(synchronize_session=False)
        db.commit()

    suffix = uuid4().hex[:10]
    try:
        _cleanup()
        org_a = Organization(name=f"IDOR P7 A {suffix}")
        org_b = Organization(name=f"IDOR P7 B {suffix}")
        db.add_all([org_a, org_b])
        db.flush()
        user_a = User(
            email=f"{EMAIL_PREFIX}a-{suffix}@{EMAIL_DOMAIN}",
            nom="User A",
            organization_id=org_a.id,
            is_active=True,
            is_platform_admin=False,
        )
        user_b = User(
            email=f"{EMAIL_PREFIX}b-{suffix}@{EMAIL_DOMAIN}",
            nom="User B",
            organization_id=org_b.id,
            is_active=True,
            is_platform_admin=False,
        )
        db.add_all([user_a, user_b])
        db.flush()
        slug_b = f"idor-p7-b-{suffix}"
        analysis_b = Analysis(
            slug=slug_b,
            analysis_number=1,
            organization_id=org_b.id,
            employee_id=user_b.id,
            company_name="Secret B",
            document_type="Kbis",
            risk_level="high",
            total_score=90,
            status="Terminée",
        )
        db.add(analysis_b)
        db.flush()
        job_b = AnalysisJob(
            organization_id=org_b.id,
            user_id=user_b.id,
            analysis_id=analysis_b.id,
            slug=slug_b,
            filename="secret.pdf",
            status="completed",
        )
        db.add(job_b)
        db.flush()
        finding_b = AnalysisFinding(
            job_id=job_b.id,
            organization_id=org_b.id,
            title="Finding B",
            detail="confidentiel",
            severity="high",
            score=80,
        )
        db.add(finding_b)
        db.flush()
        evidence_b = ComplianceEvidence(
            organization_id=org_b.id,
            finding_id=finding_b.id,
            job_id=job_b.id,
            analysis_id=analysis_b.id,
            framework_code="iso31000",
            title="Preuve B",
            status="proposed",
        )
        audit_b = GrcAudit(
            organization_id=org_b.id,
            title="Audit B",
            audit_type="internal",
            status="planned",
            created_by=user_b.id,
        )
        db.add_all([evidence_b, audit_b])
        db.commit()
        created = {
            "user_a": user_a,
            "user_b": user_b,
            "org_a": org_a.id,
            "org_b": org_b.id,
            "slug_b": slug_b,
            "job_id": job_b.id,
            "finding_id": finding_b.id,
            "evidence_id": evidence_b.id,
            "audit_id": audit_b.id,
        }
        yield db, created
    finally:
        try:
            _cleanup()
        finally:
            db.close()


def _client(user, db):
    from app.api.analysis_jobs import router as jobs_router
    from app.api.compliance_evidence import router as evidence_router
    from app.api.grc_audits import router as audits_router
    from app.core.permissions import get_current_user
    from app.database import get_db

    app = FastAPI()
    app.include_router(jobs_router)
    app.include_router(evidence_router)
    app.include_router(audits_router)
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app)


def test_live_user_a_cannot_open_job_of_b(live_db):
    db, data = live_db
    client = _client(data["user_a"], db)
    response = client.get(f"/api/v1/analysis-jobs/{data['job_id']}")
    assert response.status_code == 403


def test_live_user_a_list_jobs_hides_b(live_db):
    db, data = live_db
    client = _client(data["user_a"], db)
    jobs = client.get("/api/v1/analysis-jobs").json()["jobs"]
    assert all(job["id"] != str(data["job_id"]) for job in jobs)


def test_live_user_a_cannot_review_evidence_of_b(live_db):
    db, data = live_db
    client = _client(data["user_a"], db)
    response = client.post(
        f"/api/v1/compliance-evidence/{data['evidence_id']}/review",
        json={"status": "accepted"},
    )
    assert response.status_code == 403


def test_live_user_a_list_evidence_hides_b(live_db):
    db, data = live_db
    client = _client(data["user_a"], db)
    rows = client.get("/api/v1/compliance-evidence").json()["evidence"]
    assert all(row["id"] != str(data["evidence_id"]) for row in rows)


def test_live_user_a_cannot_open_audit_of_b(live_db):
    db, data = live_db
    client = _client(data["user_a"], db)
    response = client.get(f"/api/v1/audits/{data['audit_id']}")
    assert response.status_code == 403


def test_live_user_a_cannot_import_evidence_into_b_audit(live_db):
    db, data = live_db
    client = _client(data["user_a"], db)
    response = client.post(f"/api/v1/audits/{data['audit_id']}/import-evidence")
    assert response.status_code == 403


def test_live_user_a_cannot_access_file_slug_of_b(live_db):
    from app.core.analysis_access import assert_slug_access
    from fastapi import HTTPException

    db, data = live_db
    with pytest.raises(HTTPException) as exc:
        assert_slug_access(db, data["user_a"], data["slug_b"])
    assert exc.value.status_code == 403


def test_live_user_b_can_open_own_job_and_findings(live_db):
    db, data = live_db
    client = _client(data["user_b"], db)
    response = client.get(f"/api/v1/analysis-jobs/{data['job_id']}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(data["job_id"])
    assert any(item["id"] == str(data["finding_id"]) for item in body["findings"])


def test_live_sql_user_org_is_not_the_forged_org(live_db):
    db, data = live_db
    assert data["user_a"].organization_id == data["org_a"]
    assert data["user_a"].organization_id != data["org_b"]
    client = _client(data["user_a"], db)
    assert client.get(f"/api/v1/analysis-jobs/{data['job_id']}").status_code == 403
