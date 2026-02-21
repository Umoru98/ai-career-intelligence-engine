from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

# ── Resume Schemas ─────────────────────────────────────────────────────────────


class ResumeUploadResponse(BaseModel):
    id: uuid.UUID
    original_filename: str
    content_type: str
    size_bytes: int
    sha256: str
    extraction_status: str  # "success" | "error" | "pending"
    extraction_error: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ResumeDetail(BaseModel):
    id: uuid.UUID
    original_filename: str
    content_type: str
    size_bytes: int
    sha256: str
    cleaned_text: str | None = None
    redacted_text: str | None = None
    sections_json: dict[str, Any] | None = None
    extraction_error: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ResumeListItem(BaseModel):
    id: uuid.UUID
    original_filename: str
    content_type: str
    size_bytes: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ResumeListResponse(BaseModel):
    items: list[ResumeListItem]
    total: int
    page: int
    page_size: int


# ── Job Schemas ────────────────────────────────────────────────────────────────


class JobCreate(BaseModel):
    title: str | None = Field(None, max_length=512, examples=["Senior Python Engineer"])
    description: str = Field(
        ..., min_length=10, examples=["We are looking for a Python engineer..."]
    )


class JobResponse(BaseModel):
    id: uuid.UUID
    title: str | None = None
    description: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Analysis Schemas ───────────────────────────────────────────────────────────


class AnalysisRequest(BaseModel):
    resume_id: uuid.UUID
    job_id: uuid.UUID


class AnalysisResponse(BaseModel):
    id: uuid.UUID
    resume_id: uuid.UUID
    job_id: uuid.UUID
    match_score_percent: float = Field(..., ge=0.0, le=100.0, examples=[72.45])
    matching_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    section_summary: dict[str, Any] = Field(default_factory=dict)
    explanation: str = ""
    suggestions: list[str] = Field(default_factory=list)
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Ranking Schemas ────────────────────────────────────────────────────────────


class RankRequest(BaseModel):
    resume_ids: list[uuid.UUID] | None = Field(
        None,
        description="Subset of resume IDs to rank. If omitted, all resumes are ranked.",
    )


class RankItem(BaseModel):
    resume_id: uuid.UUID
    original_filename: str
    match_score_percent: float
    matching_skills: list[str]
    missing_skills_count: int
    explanation: str
    analysis_id: uuid.UUID


class RankResponse(BaseModel):
    job_id: uuid.UUID
    ranked: list[RankItem]


# ── Compare Schemas ────────────────────────────────────────────────────────────


class CompareRequest(BaseModel):
    resume_ids: list[uuid.UUID] = Field(..., min_length=2, max_length=20)
    job_id: uuid.UUID


class CompareResponse(BaseModel):
    job_id: uuid.UUID
    comparisons: list[AnalysisResponse]


# ── Health ─────────────────────────────────────────────────────────────────────


class HealthResponse(BaseModel):
    status: str
    version: str
    db: str
