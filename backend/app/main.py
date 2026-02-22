from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints import router as v1_router
from app.core.config import get_settings
from app.schemas.schemas import HealthResponse

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    import os
    from pathlib import Path

    # Ensure upload directory exists
    upload_path = Path(settings.upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)
    print(f"Ensuring upload directory exists at: {upload_path}")

    if settings.debug:
        from app.core.database import Base, engine
        from app.models import models  # noqa: F401 - ensure models are registered

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    yield


app = FastAPI(
    lifespan=lifespan,
    title=settings.app_name,
    version=settings.app_version,
    description="""
## AI Resume Analyzer API

A production-ready API for analyzing resumes against job descriptions.

### Features
- **Resume Upload**: PDF and DOCX support with text extraction
- **Bias-Aware Scoring**: PII redaction before embedding generation
- **Skills Matching**: Dictionary-based skills extraction and gap analysis
- **Section Detection**: Automatic resume section parsing
- **Ranking**: Rank multiple resumes against a job description
- **Comparison**: Side-by-side resume comparison

### Score Interpretation
Match scores use cosine similarity normalized to 0-100%:
- **75-100%**: Strong match
- **50-74%**: Moderate match
- **0-49%**: Weak match
    """,
    openapi_tags=[
        {"name": "resumes", "description": "Resume upload and management"},
        {"name": "jobs", "description": "Job description management"},
        {"name": "analysis", "description": "Resume analysis, ranking, and comparison"},
    ],
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(v1_router)


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check() -> HealthResponse:
    """Lightweight health check endpoint (no DB hits)."""
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        db="ignored_for_speed",
    )
