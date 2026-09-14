"""Le snapshot Alembic est présent et lisible hors Neon."""

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory


def test_alembic_baseline_head():
    ini = Path(__file__).resolve().parents[1] / "alembic.ini"
    script = ScriptDirectory.from_config(Config(str(ini)))
    assert script.get_current_head() == "0007_iso_catalog"
