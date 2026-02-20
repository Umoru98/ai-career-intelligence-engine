"""Initial schema

Revision ID: 001_initial
Revises:
Create Date: 2026-02-18

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension if available (graceful fallback)
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
    try:
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    except Exception:
        pass  # pgvector not available, embeddings stored as JSONB

    op.create_table(
        "resumes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("original_filename", sa.String(512), nullable=False),
        sa.Column("stored_path", sa.String(1024), nullable=False),
        sa.Column("content_type", sa.String(128), nullable=False),
        sa.Column("size_bytes", sa.Integer, nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("raw_extracted_text", sa.Text, nullable=True),
        sa.Column("cleaned_text", sa.Text, nullable=True),
        sa.Column("redacted_text", sa.Text, nullable=True),
        sa.Column("sections_json", postgresql.JSONB, nullable=True),
        sa.Column("extraction_error", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_resumes_sha256", "resumes", ["sha256"])
    op.create_index("ix_resumes_created_at", "resumes", ["created_at"])

    op.create_table(
        "jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("title", sa.Text, nullable=True),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_jobs_created_at", "jobs", ["created_at"])

    op.create_table(
        "embeddings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("owner_type", sa.String(16), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("embedding_json", postgresql.JSONB, nullable=True),
        sa.Column("model_name", sa.String(256), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_embeddings_owner_id", "embeddings", ["owner_id"])
    op.create_index("ix_embeddings_owner_type_owner_id", "embeddings", ["owner_type", "owner_id"])

    op.create_table(
        "analyses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("resume_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("match_score_percent", sa.Float, nullable=False),
        sa.Column("matching_skills", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("missing_skills", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("section_summary", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("explanation", sa.Text, nullable=False, server_default=""),
        sa.Column("suggestions", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_analyses_resume_id", "analyses", ["resume_id"])
    op.create_index("ix_analyses_job_id", "analyses", ["job_id"])
    op.create_index("ix_analyses_created_at", "analyses", ["created_at"])


def downgrade() -> None:
    op.drop_table("analyses")
    op.drop_table("embeddings")
    op.drop_table("jobs")
    op.drop_table("resumes")
