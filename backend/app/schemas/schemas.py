from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# ── Resume Schemas ─────────────────────────────────────────────────────────────

class ResumeUploadResponse(BaseModel):
    id: uuid.UUID
    original_filename: str
    content_type: str
    size_bytes: int
    sha256: str
    extraction_status: str  # "success" | "error" | "pending"
    extraction_error: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ResumeDetail(BaseModel):
    id: uuid.UUID
    original_filename: str
    content_type: str
    size_bytes: int
    sha256: str
    cleaned_text: Optional[str] = None
    redacted_text: Optional[str] = None
    sections_json: Optional[Dict[str, Any]] = None
    extraction_error: Optional[str] = None
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
    items: List[ResumeListItem]
    total: int
    page: int
    page_size: int


# ── Job Schemas ────────────────────────────────────────────────────────────────

class JobCreate(BaseModel):
    title: Optional[str] = Field(None, max_length=512, examples=["Senior Python Engineer"])
    description: str = Field(..., min_length=10, examples=["We are looking for a Python engineer..."])


class JobResponse(BaseModel):
    id: uuid.UUID
    title: Optional[str] = None
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
    matching_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    section_summary: Dict[str, Any] = Field(default_factory=dict)
    explanation: str = ""
    suggestions: List[str] = Field(default_factory=list)
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Ranking Schemas ────────────────────────────────────────────────────────────

class RankRequest(BaseModel):
    resume_ids: Optional[List[uuid.UUID]] = Field(
        None,
        description="Subset of resume IDs to rank. If omitted, all resumes are ranked.",
    )


class RankItem(BaseModel):
    resume_id: uuid.UUID
    original_filename: str
    match_score_percent: float
    matching_skills: List[str]
    missing_skills_count: int
    explanation: str
    analysis_id: uuid.UUID


class RankResponse(BaseModel):
    job_id: uuid.UUID
    ranked: List[RankItem]


# ── Compare Schemas ────────────────────────────────────────────────────────────

class CompareRequest(BaseModel):
    resume_ids: List[uuid.UUID] = Field(..., min_length=2, max_length=20)
    job_id: uuid.UUID


class CompareResponse(BaseModel):
    job_id: uuid.UUID
    comparisons: List[AnalysisResponse]


# ── Health ─────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str
    db: str
