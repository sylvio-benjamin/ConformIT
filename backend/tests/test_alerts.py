from types import SimpleNamespace
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.alerts import router as alerts_router
from app.core.permissions import get_current_user


def test_high_risk_alert_noop_without_webhook(monkeypatch):
    monkeypatch.setattr("app.api.alerts.MAKE_WEBHOOK_URL", "")
    app = FastAPI()
    app.include_router(alerts_router)
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=uuid4(),
        email="a@example.test",
        organization_id=uuid4(),
        is_platform_admin=False,
        is_active=True,
    )
    client = TestClient(app)
    response = client.post(
        "/api/v1/alerts/high-risk",
        json={"entreprise": "Acme", "risque": "high", "score": 80, "rcs": ""},
    )
    assert response.status_code == 200
    assert response.json()["sent"] is False
    assert response.json()["reason"] == "webhook_disabled"


def test_high_risk_alert_requires_auth():
    app = FastAPI()
    app.include_router(alerts_router)
    client = TestClient(app)
    response = client.post(
        "/api/v1/alerts/high-risk",
        json={"entreprise": "Acme", "risque": "high"},
    )
    assert response.status_code == 401
