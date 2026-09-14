"""P8 drop users.firebase_uid after runtime consumers were removed.

Revision ID: 0006_drop_firebase_uid
Revises: 0005_audits
Create Date: 2026-09-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0006_drop_firebase_uid"
down_revision: Union[str, None] = "0005_audits"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("users"):
        return
    columns = {col["name"] for col in inspector.get_columns("users")}
    if "firebase_uid" not in columns:
        return
    for index in inspector.get_indexes("users"):
        if "firebase_uid" in (index.get("column_names") or []):
            op.drop_index(index["name"], table_name="users")
    for constraint in inspector.get_unique_constraints("users"):
        if "firebase_uid" in (constraint.get("column_names") or []):
            op.drop_constraint(constraint["name"], "users", type_="unique")
    op.drop_column("users", "firebase_uid")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("users"):
        return
    columns = {col["name"] for col in inspector.get_columns("users")}
    if "firebase_uid" in columns:
        return
    op.add_column("users", sa.Column("firebase_uid", sa.String(255), nullable=True))
    op.create_index(
        "idx_users_firebase_uid",
        "users",
        ["firebase_uid"],
        unique=True,
        postgresql_where=sa.text("firebase_uid IS NOT NULL"),
    )
