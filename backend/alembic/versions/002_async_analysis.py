"""Add analysis status and error message

Revision ID: 002_async_analysis
Revises: 001_initial
Create Date: 2026-02-21

"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "002_async_analysis"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add status and error_message columns
    op.add_column("analyses", sa.Column("status", sa.String(length=20), nullable=False, server_default="done"))
    op.add_column("analyses", sa.Column("error_message", sa.Text(), nullable=True))
    
    # Make match results nullable (for queued jobs)
    op.alter_column("analyses", "match_score_percent", existing_type=sa.Float(), nullable=True)
    op.alter_column("analyses", "matching_skills", existing_type=postgresql.JSONB(), nullable=True, server_default=None)
    op.alter_column("analyses", "missing_skills", existing_type=postgresql.JSONB(), nullable=True, server_default=None)
    op.alter_column("analyses", "section_summary", existing_type=postgresql.JSONB(), nullable=True, server_default=None)
    op.alter_column("analyses", "explanation", existing_type=sa.Text(), nullable=True, server_default=None)
    op.alter_column("analyses", "suggestions", existing_type=postgresql.JSONB(), nullable=True, server_default=None)


def downgrade() -> None:
    op.drop_column("analyses", "error_message")
    op.drop_column("analyses", "status")
    
    # Reverting nullability would require filling data, skipping for simplicity in this MVP upgrade
    op.alter_column("analyses", "match_score_percent", existing_type=sa.Float(), nullable=False)
