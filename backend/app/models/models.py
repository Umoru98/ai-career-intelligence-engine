from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    stored_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    content_type: Mapped[str] = mapped_column(String(128), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    raw_extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    cleaned_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    redacted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    sections_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    extraction_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    embeddings: Mapped[list[Embedding]] = relationship(
        "Embedding",
        back_populates="resume",
        cascade="all, delete-orphan",
        primaryjoin="and_(Embedding.owner_id == Resume.id, Embedding.owner_type == 'resume')",
        foreign_keys="[Embedding.owner_id]",
        overlaps="job_embeddings",
    )
    analyses: Mapped[list[Analysis]] = relationship(
        "Analysis", back_populates="resume", cascade="all, delete-orphan"
    )


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    analyses: Mapped[list[Analysis]] = relationship(
        "Analysis", back_populates="job", cascade="all, delete-orphan"
    )


class Embedding(Base):
    __tablename__ = "embeddings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_type: Mapped[str] = mapped_column(String(16), nullable=False)  # 'resume' | 'job'
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    embedding_json: Mapped[list | None] = mapped_column(
        JSONB, nullable=True
    )  # float[] stored as JSON
    model_name: Mapped[str] = mapped_column(String(256), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Polymorphic relationships via owner_type
    resume: Mapped[Resume | None] = relationship(
        "Resume",
        back_populates="embeddings",
        primaryjoin="and_(Embedding.owner_id == Resume.id, Embedding.owner_type == 'resume')",
        foreign_keys="[Embedding.owner_id]",
        overlaps="job_embeddings",
    )


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="queued")  # queued | running | done | failed
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    match_score_percent: Mapped[float | None] = mapped_column(nullable=True)
    matching_skills: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    missing_skills: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    section_summary: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    suggestions: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    result_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), index=True
    )


    resume: Mapped[Resume] = relationship("Resume", back_populates="analyses")
    job: Mapped[Job] = relationship("Job", back_populates="analyses")
