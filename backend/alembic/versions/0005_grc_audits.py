"""P6 structured GRC audits and audit findings.

Revision ID: 0005_audits
Revises: 0004_evidence
Create Date: 2026-09-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0005_audits"
down_revision: Union[str, None] = "0004_evidence"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(name)


def upgrade() -> None:
    if not _table_exists("audits"):
        op.create_table(
            "audits",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
            sa.Column("title", sa.String(255), nullable=False),
            sa.Column("audit_type", sa.String(50), nullable=False, server_default="internal"),
            sa.Column("framework_code", sa.String(50)),
            sa.Column("status", sa.String(50), nullable=False, server_default="planned"),
            sa.Column("scope", sa.Text()),
            sa.Column("auditor_name", sa.String(255)),
            sa.Column("started_at", sa.DateTime(timezone=True)),
            sa.Column("finished_at", sa.DateTime(timezone=True)),
            sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_audits_organization_id", "audits", ["organization_id"])
        op.create_index("ix_audits_status", "audits", ["status"])
    if not _table_exists("audit_findings"):
        op.create_table(
            "audit_findings",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("audit_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("audits.id", ondelete="CASCADE"), nullable=False),
            sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
            sa.Column("evidence_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("compliance_evidence.id", ondelete="SET NULL"), nullable=True),
            sa.Column("title", sa.String(255), nullable=False),
            sa.Column("detail", sa.Text()),
            sa.Column("severity", sa.String(50)),
            sa.Column("status", sa.String(50), nullable=False, server_default="open"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_audit_findings_audit_id", "audit_findings", ["audit_id"])
        op.create_index("ix_audit_findings_organization_id", "audit_findings", ["organization_id"])
        op.create_index("ix_audit_findings_status", "audit_findings", ["status"])


def downgrade() -> None:
    if _table_exists("audit_findings"):
        op.drop_index("ix_audit_findings_status", table_name="audit_findings")
        op.drop_index("ix_audit_findings_organization_id", table_name="audit_findings")
        op.drop_index("ix_audit_findings_audit_id", table_name="audit_findings")
        op.drop_table("audit_findings")
    if _table_exists("audits"):
        op.drop_index("ix_audits_status", table_name="audits")
        op.drop_index("ix_audits_organization_id", table_name="audits")
        op.drop_table("audits")
