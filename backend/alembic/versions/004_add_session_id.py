"""Add session_id to resumes and analyses

Revision ID: 004_add_session_id
Revises: 003_result_json_updated_at
Create Date: 2026-02-23

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "004_add_session_id"
down_revision = "003_result_json_updated_at"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add session_id to resumes
    op.add_column("resumes", sa.Column("session_id", sa.String(length=255), nullable=True))
    op.create_index(op.f("ix_resumes_session_id"), "resumes", ["session_id"], unique=False)
    
    # Add session_id to analyses
    op.add_column("analyses", sa.Column("session_id", sa.String(length=255), nullable=True))
    op.create_index(op.f("ix_analyses_session_id"), "analyses", ["session_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_analyses_session_id"), table_name="analyses")
    op.drop_column("analyses", "session_id")
    op.drop_index(op.f("ix_resumes_session_id"), table_name="resumes")
    op.drop_column("resumes", "session_id")
