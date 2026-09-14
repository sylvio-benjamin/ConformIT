"""P5 compliance evidence and risk treatments.

Revision ID: 0004_evidence
Revises: 0003_analysis_jobs
Create Date: 2026-09-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0004_evidence"
down_revision: Union[str, None] = "0003_analysis_jobs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(name)


def upgrade() -> None:
    if not _table_exists("compliance_evidence"):
        op.create_table(
            "compliance_evidence",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
            sa.Column("finding_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("analysis_findings.id", ondelete="SET NULL"), nullable=True),
            sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("analysis_jobs.id", ondelete="SET NULL"), nullable=True),
            sa.Column("analysis_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("analyses.id", ondelete="SET NULL"), nullable=True),
            sa.Column("framework_code", sa.String(50)),
            sa.Column("applicable_frameworks", postgresql.JSONB()),
            sa.Column("title", sa.String(255), nullable=False),
            sa.Column("detail", sa.Text()),
            sa.Column("severity", sa.String(50)),
            sa.Column("status", sa.String(50), nullable=False, server_default="proposed"),
            sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("reviewed_at", sa.DateTime(timezone=True)),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_compliance_evidence_organization_id", "compliance_evidence", ["organization_id"])
        op.create_index("ix_compliance_evidence_finding_id", "compliance_evidence", ["finding_id"])
        op.create_index("ix_compliance_evidence_job_id", "compliance_evidence", ["job_id"])
        op.create_index("ix_compliance_evidence_framework_code", "compliance_evidence", ["framework_code"])
        op.create_index("ix_compliance_evidence_status", "compliance_evidence", ["status"])
    if not _table_exists("risk_treatments"):
        op.create_table(
            "risk_treatments",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
            sa.Column("risk_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("risks.id", ondelete="CASCADE"), nullable=False),
            sa.Column("strategy", sa.String(50), nullable=False),
            sa.Column("description", sa.Text()),
            sa.Column("status", sa.String(50), nullable=False, server_default="planned"),
            sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("due_date", sa.DateTime(timezone=True)),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_risk_treatments_organization_id", "risk_treatments", ["organization_id"])
        op.create_index("ix_risk_treatments_risk_id", "risk_treatments", ["risk_id"])
        op.create_index("ix_risk_treatments_status", "risk_treatments", ["status"])


def downgrade() -> None:
    if _table_exists("risk_treatments"):
        op.drop_index("ix_risk_treatments_status", table_name="risk_treatments")
        op.drop_index("ix_risk_treatments_risk_id", table_name="risk_treatments")
        op.drop_index("ix_risk_treatments_organization_id", table_name="risk_treatments")
        op.drop_table("risk_treatments")
    if _table_exists("compliance_evidence"):
        op.drop_index("ix_compliance_evidence_status", table_name="compliance_evidence")
        op.drop_index("ix_compliance_evidence_framework_code", table_name="compliance_evidence")
        op.drop_index("ix_compliance_evidence_job_id", table_name="compliance_evidence")
        op.drop_index("ix_compliance_evidence_finding_id", table_name="compliance_evidence")
        op.drop_index("ix_compliance_evidence_organization_id", table_name="compliance_evidence")
        op.drop_table("compliance_evidence")
