"""P3 organization profile, applicability, kb_controls.

Revision ID: 0002_applicability
Revises: 0001_baseline
Create Date: 2026-09-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002_applicability"
down_revision: Union[str, None] = "0001_baseline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(name)


def upgrade() -> None:
    if not _table_exists("organization_profiles"):
        op.create_table(
            "organization_profiles",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, unique=True),
            sa.Column("sector", sa.String(100)),
            sa.Column("size", sa.String(50)),
            sa.Column("country", sa.String(2)),
            sa.Column("criticality", sa.String(50)),
            sa.Column("processes_personal_data", sa.Boolean(), server_default=sa.text("false")),
            sa.Column("hosting", sa.String(50)),
            sa.Column("listed_company", sa.Boolean(), server_default=sa.text("false")),
            sa.Column("notes", sa.Text()),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
    if not _table_exists("applicability_rules"):
        op.create_table(
            "applicability_rules",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("code", sa.String(80), nullable=False, unique=True),
            sa.Column("framework_code", sa.String(50), nullable=False),
            sa.Column("condition", postgresql.JSONB(), nullable=False),
            sa.Column("reason", sa.Text(), nullable=False),
            sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
    if not _table_exists("applicability_decisions"):
        op.create_table(
            "applicability_decisions",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
            sa.Column("framework_code", sa.String(50), nullable=False),
            sa.Column("applicable", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("reason", sa.Text()),
            sa.Column("confidence", sa.Float(), server_default="0.8"),
            sa.Column("source_rule", sa.String(80)),
            sa.Column("override", sa.Boolean(), server_default=sa.text("false")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.UniqueConstraint("organization_id", "framework_code", name="uq_applicability_org_framework"),
        )
        op.create_index("ix_applicability_decisions_organization_id", "applicability_decisions", ["organization_id"])
    if not _table_exists("kb_controls"):
        op.create_table(
            "kb_controls",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("code", sa.String(80), nullable=False, unique=True),
            sa.Column("title", sa.String(255), nullable=False),
            sa.Column("description", sa.Text()),
            sa.Column("framework_code", sa.String(50), nullable=False),
            sa.Column("control_type", sa.String(50)),
            sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )


def downgrade() -> None:
    if _table_exists("kb_controls"):
        op.drop_table("kb_controls")
    if _table_exists("applicability_decisions"):
        op.drop_index("ix_applicability_decisions_organization_id", table_name="applicability_decisions")
        op.drop_table("applicability_decisions")
    if _table_exists("applicability_rules"):
        op.drop_table("applicability_rules")
    if _table_exists("organization_profiles"):
        op.drop_table("organization_profiles")
