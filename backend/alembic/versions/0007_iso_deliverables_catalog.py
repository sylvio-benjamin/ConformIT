"""Catalogue ISO Open Data (métadonnées uniquement).

Revision ID: 0007_iso_catalog
Revises: 0006_drop_firebase_uid
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

revision: str = "0007_iso_catalog"
down_revision: Union[str, None] = "0006_drop_firebase_uid"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(name: str) -> bool:
    bind = op.get_bind()
    return name in inspect(bind).get_table_names()


def upgrade() -> None:
    if _table_exists("iso_deliverables"):
        return
    op.create_table(
        "iso_deliverables",
        sa.Column("iso_id", sa.Integer(), primary_key=True),
        sa.Column("reference", sa.String(255), nullable=False),
        sa.Column("title_en", sa.Text()),
        sa.Column("title_fr", sa.Text()),
        sa.Column("deliverable_type", sa.String(20)),
        sa.Column("supplement_type", sa.String(20)),
        sa.Column("edition", sa.Integer()),
        sa.Column("publication_date", sa.Date()),
        sa.Column("ics_codes", postgresql.JSONB(), nullable=True),
        sa.Column("owner_committee", sa.String(120)),
        sa.Column("current_stage", sa.Integer()),
        sa.Column("replaces", postgresql.JSONB(), nullable=True),
        sa.Column("replaced_by", postgresql.JSONB(), nullable=True),
        sa.Column("languages", postgresql.JSONB(), nullable=True),
        sa.Column("pages_en", sa.Integer()),
        sa.Column("scope_en", sa.Text()),
        sa.Column("withdrawn", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("framework_code", sa.String(50)),
        sa.Column("metadata_source", sa.String(80)),
        sa.Column("official_source", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_iso_deliverables_reference", "iso_deliverables", ["reference"])
    op.create_index("ix_iso_deliverables_withdrawn", "iso_deliverables", ["withdrawn"])
    op.create_index("ix_iso_deliverables_framework_code", "iso_deliverables", ["framework_code"])


def downgrade() -> None:
    if _table_exists("iso_deliverables"):
        op.drop_index("ix_iso_deliverables_framework_code", table_name="iso_deliverables")
        op.drop_index("ix_iso_deliverables_withdrawn", table_name="iso_deliverables")
        op.drop_index("ix_iso_deliverables_reference", table_name="iso_deliverables")
        op.drop_table("iso_deliverables")
