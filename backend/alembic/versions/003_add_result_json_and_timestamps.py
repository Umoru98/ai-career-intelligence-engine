"""Add result_json and updated_at to analysis

Revision ID: 003_result_json_updated_at
Revises: 002_async_analysis
Create Date: 2026-02-21

"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "003_result_json_updated_at"
down_revision = "002_async_analysis"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add columns as nullable first
    op.add_column("analyses", sa.Column("result_json", postgresql.JSONB(), nullable=True))
    op.add_column("analyses", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True))

    # Create index for updated_at
    op.create_index(op.f("ix_analyses_updated_at"), "analyses", ["updated_at"], unique=False)
    
    # Update updated_at to match created_at for existing rows
    op.execute("UPDATE analyses SET updated_at = created_at WHERE updated_at IS NULL")
    
    # Make updated_at non-nullable
    op.alter_column("analyses", "updated_at", nullable=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_analyses_updated_at"), table_name="analyses")
    op.drop_column("analyses", "updated_at")
    op.drop_column("analyses", "result_json")
