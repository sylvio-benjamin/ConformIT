"""Isolation multi-tenant : auth requise + assert_same_organization."""

from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.core.permissions import assert_same_organization, require_admin
from app.database import get_db


def _user(org_id, *, admin=False):
    return SimpleNamespace(
        id=uuid4(),
        organization_id=org_id,
        is_platform_admin=admin,
        is_active=True,
    )


def test_same_organization_allowed():
    org = uuid4()
    assert_same_organization(_user(org), org)


def test_other_organization_forbidden():
    with pytest.raises(HTTPException) as exc:
        assert_same_organization(_user(uuid4()), uuid4())
    assert exc.value.status_code == 403


def test_missing_organization_forbidden():
    with pytest.raises(HTTPException) as exc:
        assert_same_organization(_user(uuid4()), None)
    assert exc.value.status_code == 403


def test_platform_admin_bypasses_org_check():
    assert_same_organization(_user(uuid4(), admin=True), uuid4())


def test_require_admin_rejects_member():
    with pytest.raises(HTTPException) as exc:
        require_admin(user=_user(uuid4()))
    assert exc.value.status_code == 403


def test_require_admin_accepts_platform_admin():
    admin = _user(uuid4(), admin=True)
    assert require_admin(user=admin) is admin


def _unauthenticated_client():
    from app.api.analyses import router as analyses_router
    from app.api.risks import router as risks_router
    from app.api.controls import router as controls_router

    app = FastAPI()
    app.include_router(analyses_router)
    app.include_router(risks_router)
    app.include_router(controls_router)

    def _no_db():
        yield None

    app.dependency_overrides[get_db] = _no_db
    return TestClient(app)


@pytest.mark.parametrize("path", [
    "/api/analyses",
    "/api/risks",
    "/api/controls",
])
def test_protected_lists_require_auth(path):
    client = _unauthenticated_client()
    response = client.get(path)
    assert response.status_code == 401


def test_analysis_from_other_org_is_forbidden():
    from app.api.analyses import router as analyses_router
    from app.core.permissions import get_current_user

    org_a = uuid4()
    org_b = uuid4()
    visitor = _user(org_a)

    class _Query:
        def filter(self, *_args, **_kwargs):
            return self

        def first(self):
            return SimpleNamespace(
                organization_id=org_b,
                slug="autre-orga",
                analysis_number=1,
                id=uuid4(),
                company_name="Secret SA",
                document_type="Kbis",
                rcs="",
                total_score=10,
                risk_level="high",
                precision=None,
                quality=None,
                filename=None,
                risk_color=None,
                status="Terminée",
                details=[],
                created_at=None,
            )

    class _Session:
        def query(self, *_args, **_kwargs):
            return _Query()

    app = FastAPI()
    app.include_router(analyses_router)
    app.dependency_overrides[get_db] = lambda: _Session()
    app.dependency_overrides[get_current_user] = lambda: visitor
    client = TestClient(app)

    response = client.get("/api/analyses/autre-orga")
    assert response.status_code == 403


class _FirstSession:
    def __init__(self, row):
        self.row = row

    def query(self, *_args, **_kwargs):
        return self

    def filter(self, *_args, **_kwargs):
        return self

    def order_by(self, *_args, **_kwargs):
        return self

    def first(self):
        return self.row


def _client_for(router, visitor, session):
    from app.core.permissions import get_current_user

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = lambda: session
    app.dependency_overrides[get_current_user] = lambda: visitor
    return TestClient(app)


def test_job_from_other_org_is_forbidden():
    from app.api.analysis_jobs import router

    org_b = uuid4()
    job_id = uuid4()
    client = _client_for(
        router,
        _user(uuid4()),
        _FirstSession(SimpleNamespace(id=job_id, organization_id=org_b)),
    )
    response = client.get(f"/api/v1/analysis-jobs/{job_id}")
    assert response.status_code == 403


def test_evidence_review_from_other_org_is_forbidden():
    from app.api.compliance_evidence import router

    evidence_id = uuid4()
    client = _client_for(
        router,
        _user(uuid4()),
        _FirstSession(SimpleNamespace(id=evidence_id, organization_id=uuid4())),
    )
    response = client.post(
        f"/api/v1/compliance-evidence/{evidence_id}/review",
        json={"status": "accepted"},
    )
    assert response.status_code == 403


def test_audit_from_other_org_is_forbidden():
    from app.api.grc_audits import router

    audit_id = uuid4()
    client = _client_for(
        router,
        _user(uuid4()),
        _FirstSession(SimpleNamespace(id=audit_id, organization_id=uuid4())),
    )
    response = client.get(f"/api/v1/audits/{audit_id}")
    assert response.status_code == 403


def test_file_slug_from_other_org_is_forbidden():
    from app.core.analysis_access import assert_slug_access

    visitor = _user(uuid4())
    session = _FirstSession(
        SimpleNamespace(organization_id=uuid4(), slug="secret-b"),
    )
    with pytest.raises(HTTPException) as exc:
        assert_slug_access(session, visitor, "secret-b")
    assert exc.value.status_code == 403


def test_unknown_slug_is_not_open():
    from app.core.analysis_access import assert_slug_access

    session = _FirstSession(None)
    with pytest.raises(HTTPException) as exc:
        assert_slug_access(session, _user(uuid4()), "inconnu")
    assert exc.value.status_code == 404


@pytest.mark.parametrize("path", [
    "/api/v1/analysis-jobs",
    "/api/v1/compliance-evidence",
    "/api/v1/audits",
])
def test_p7_lists_require_auth(path):
    from app.api.analysis_jobs import router as jobs_router
    from app.api.compliance_evidence import router as evidence_router
    from app.api.grc_audits import router as audits_router

    app = FastAPI()
    app.include_router(jobs_router)
    app.include_router(evidence_router)
    app.include_router(audits_router)
    app.dependency_overrides[get_db] = lambda: None
    client = TestClient(app)
    assert client.get(path).status_code == 401
