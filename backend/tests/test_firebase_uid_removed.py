"""P8 : plus aucun consommateur runtime de users.firebase_uid."""

from pathlib import Path
from uuid import uuid4

from alembic.config import Config
from alembic.script import ScriptDirectory

from app.models.organizations import User
from app.services.plan_service import _find_user


def test_user_model_has_no_firebase_uid():
    assert "firebase_uid" not in User.__table__.c


def test_find_user_rejects_non_uuid():
    class _Boom:
        def query(self, *_args, **_kwargs):
            raise AssertionError("ne doit pas interroger la base pour un uid Firebase")

    assert _find_user(_Boom(), "legacy-firebase-uid") is None


def test_find_user_queries_primary_key():
    user_id = uuid4()
    seen = {}

    class _Query:
        def filter(self, criterion):
            seen["criterion"] = str(criterion)
            return self

        def first(self):
            return None

    class _Session:
        def query(self, model):
            seen["model"] = model
            return _Query()

    assert _find_user(_Session(), str(user_id)) is None
    assert seen["model"] is User
    assert "firebase_uid" not in seen["criterion"]
    assert "users.id" in seen["criterion"]


def test_runtime_sources_have_no_firebase_uid_column():
    root = Path(__file__).resolve().parents[1] / "app"
    offenders = []
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "firebase_uid" in text:
            offenders.append(str(path.relative_to(root.parent)))
    assert offenders == []


def test_alembic_head_drops_firebase_uid():
    ini = Path(__file__).resolve().parents[1] / "alembic.ini"
    script = ScriptDirectory.from_config(Config(str(ini)))
    revisions = [rev.revision for rev in script.walk_revisions()]
    assert "0006_drop_firebase_uid" in revisions
    assert script.get_current_head() == "0007_iso_catalog"
