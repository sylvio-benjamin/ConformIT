"""Baseline after Firebase runtime removal.

The existing schema is created/patched by app.database.init_db().
This revision stamps that snapshot so future tables go through Alembic.

Revision ID: 0001_baseline
Revises:
Create Date: 2026-09-12
"""
from typing import Sequence, Union

revision: str = "0001_baseline"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
