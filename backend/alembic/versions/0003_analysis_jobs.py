"""P4 analysis jobs, findings, document storage metadata.

Revision ID: 0003_analysis_jobs
Revises: 0002_applicability
Create Date: 2026-09-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0003_analysis_jobs"
down_revision: Union[str, None] = "0002_applicability"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(name)


def _column_names(table: str) -> set:
    return {col["name"] for col in sa.inspect(op.get_bind()).get_columns(table)}


def upgrade() -> None:
    if not _table_exists("analysis_jobs"):
        _create_analysis_jobs()
    if not _table_exists("analysis_findings"):
        _create_analysis_findings()
    _add_document_columns()


def _create_analysis_jobs() -> None:
    op.create_table(
        "analysis_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("analysis_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("analyses.id", ondelete="SET NULL"), nullable=True),
        sa.Column("slug", sa.String(255)),
        sa.Column("filename", sa.String(255)),
        sa.Column("storage_key", sa.String(500)),
        sa.Column("status", sa.String(50), nullable=False, server_default="queued"),
        sa.Column("error_message", sa.Text()),
        sa.Column("result_summary", postgresql.JSONB()),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_analysis_jobs_organization_id", "analysis_jobs", ["organization_id"])
    op.create_index("ix_analysis_jobs_user_id", "analysis_jobs", ["user_id"])
    op.create_index("ix_analysis_jobs_slug", "analysis_jobs", ["slug"])
    op.create_index("ix_analysis_jobs_status", "analysis_jobs", ["status"])


def _create_analysis_findings() -> None:
    op.create_table(
        "analysis_findings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("analysis_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("detail", sa.Text()),
        sa.Column("severity", sa.String(50)),
        sa.Column("score", sa.Integer()),
        sa.Column("source_question", sa.String(255)),
        sa.Column("evidence", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_analysis_findings_job_id", "analysis_findings", ["job_id"])
    op.create_index("ix_analysis_findings_organization_id", "analysis_findings", ["organization_id"])


def _add_document_columns() -> None:
    if not _table_exists("documents"):
        return
    cols = _column_names("documents")
    if "storage_key" not in cols:
        op.add_column("documents", sa.Column("storage_key", sa.String(500), nullable=True))
    if "original_filename" not in cols:
        op.add_column("documents", sa.Column("original_filename", sa.String(255), nullable=True))
    if "mime_type" not in cols:
        op.add_column("documents", sa.Column("mime_type", sa.String(120), nullable=True))
    if "byte_size" not in cols:
        op.add_column("documents", sa.Column("byte_size", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("documents", "byte_size")
    op.drop_column("documents", "mime_type")
    op.drop_column("documents", "original_filename")
    op.drop_column("documents", "storage_key")
    op.drop_index("ix_analysis_findings_organization_id", table_name="analysis_findings")
    op.drop_index("ix_analysis_findings_job_id", table_name="analysis_findings")
    op.drop_table("analysis_findings")
    op.drop_index("ix_analysis_jobs_status", table_name="analysis_jobs")
    op.drop_index("ix_analysis_jobs_slug", table_name="analysis_jobs")
    op.drop_index("ix_analysis_jobs_user_id", table_name="analysis_jobs")
    op.drop_index("ix_analysis_jobs_organization_id", table_name="analysis_jobs")
    op.drop_table("analysis_jobs")
