from app.core.health import liveness, readiness


def test_liveness_does_not_need_db():
    assert liveness() == {"status": "ok"}


def test_ready_reports_db_down(monkeypatch):
    def _fail():
        raise RuntimeError("db down")

    monkeypatch.setattr("app.database.ping_db", _fail)
    payload, code = readiness()
    assert code == 503
    assert payload["postgresql"] is False
    assert payload["status"] == "not_ready"


def test_ready_reports_db_up(monkeypatch):
    monkeypatch.setattr("app.database.ping_db", lambda: True)
    payload, code = readiness()
    assert code == 200
    assert payload["postgresql"] is True
    assert payload["status"] == "ready"
