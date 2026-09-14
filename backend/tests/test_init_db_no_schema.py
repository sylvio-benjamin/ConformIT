from pathlib import Path

from app.database import init_db


def test_init_db_source_has_no_implicit_ddl():
    source = (Path(__file__).resolve().parents[1] / "app" / "database.py").read_text(encoding="utf-8")
    body = source.split("def init_db()", 1)[1].split("def get_db", 1)[0]
    assert "create_all" not in body
    assert "ALTER TABLE" not in body
    assert "CREATE INDEX" not in body


def test_init_db_is_idempotent():
    init_db()
    init_db()
