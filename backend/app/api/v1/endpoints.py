from __future__ import annotations

import uuid

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Header,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.models.models import Analysis, Job, Resume
from app.schemas.schemas import (
    AnalysisRequest,
    AnalysisResponse,
    CompareRequest,
    CompareResponse,
    JobCreate,
    JobResponse,
    RankItem,
    RankRequest,
    RankResponse,
    ResumeDetail,
    ResumeListItem,
    ResumeListResponse,
    ResumeUploadResponse,
)
from app.services.analyzer import rank_resumes, run_analysis
from app.services.extractor import clean_text, extract_text
from app.services.nlp_pipeline import detect_sections
from app.services.redactor import redact_text
from app.utils.file_storage import ALLOWED_CONTENT_TYPES, save_upload_file

settings = get_settings()
router = APIRouter(prefix="/v1", tags=["v1"])


async def get_session_id(x_session_id: str | None = Header(None)) -> str | None:
    return x_session_id


# ── Resumes ────────────────────────────────────────────────────────────────────


@router.post(
    "/resumes/upload",
    response_model=ResumeUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a resume (PDF or DOCX)",
    tags=["resumes"],
)
async def upload_resume(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db),
    session_id: str | None = Depends(get_session_id),
) -> ResumeUploadResponse:
    # Validate content type
    content_type = file.content_type or ""
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {content_type}. Allowed: PDF, DOCX.",
        )

    # Read file and validate size
    file_bytes = await file.read()
    if len(file_bytes) > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {settings.max_file_size_mb}MB.",
        )

    # Save to disk
    import io

    file_obj = io.BytesIO(file_bytes)
    stored_path, sha256, size_bytes = await save_upload_file(
        file_obj, file.filename or "resume", content_type
    )

    # Extract text
    extraction_error: str | None = None
    raw_text: str | None = None
    cleaned: str | None = None
    redacted: str | None = None
    sections: dict | None = None

    try:
        import asyncio
        raw_text = extract_text(stored_path, content_type)
        cleaned = clean_text(raw_text)
        # Redaction runs SpaCy NER which is heavy CPU, offload to thread
        redacted = await asyncio.to_thread(redact_text, cleaned)
        sections = detect_sections(redacted)
    except Exception as e:
        extraction_error = str(e)

    # Persist to DB
    resume = Resume(
        original_filename=file.filename or "resume",
        stored_path=stored_path,
        content_type=content_type,
        size_bytes=size_bytes,
        sha256=sha256,
        raw_extracted_text=raw_text,
        cleaned_text=cleaned,
        redacted_text=redacted,
        sections_json=sections,
        extraction_error=extraction_error,
        session_id=session_id,
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)

    return ResumeUploadResponse(
        id=resume.id,
        original_filename=resume.original_filename,
        content_type=resume.content_type,
        size_bytes=resume.size_bytes,
        sha256=resume.sha256,
        extraction_status="error" if extraction_error else "success",
        extraction_error=extraction_error,
        created_at=resume.created_at,
    )


@router.get(
    "/resumes",
    response_model=ResumeListResponse,
    summary="List all resumes",
    tags=["resumes"],
)
async def list_resumes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    session_id: str | None = Depends(get_session_id),
) -> ResumeListResponse:
    offset = (page - 1) * page_size
    total = await db.scalar(
        select(func.count()).select_from(Resume).where(Resume.session_id == session_id)
    )
    result = await db.execute(
        select(Resume)
        .where(Resume.session_id == session_id)
        .order_by(Resume.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    resumes = result.scalars().all()
    return ResumeListResponse(
        items=[ResumeListItem.model_validate(r) for r in resumes],
        total=total or 0,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/resumes/{resume_id}",
    response_model=ResumeDetail,
    summary="Get resume details",
    tags=["resumes"],
)
async def get_resume(
    resume_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    session_id: str | None = Depends(get_session_id),
) -> ResumeDetail:
    resume = await db.get(Resume, resume_id)
    if not resume or resume.session_id != session_id:
        raise HTTPException(status_code=404, detail="Resume not found.")
    return ResumeDetail.model_validate(resume)


# ── Jobs ───────────────────────────────────────────────────────────────────────


@router.post(
    "/jobs",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a job description",
    tags=["jobs"],
)
async def create_job(
    payload: JobCreate,
    db: AsyncSession = Depends(get_db),
) -> JobResponse:
    job = Job(title=payload.title, description=payload.description)
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return JobResponse.model_validate(job)


@router.get(
    "/jobs/{job_id}",
    response_model=JobResponse,
    summary="Get job description",
    tags=["jobs"],
)
async def get_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> JobResponse:
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return JobResponse.model_validate(job)


# ── Analysis ───────────────────────────────────────────────────────────────────


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Analyze one resume against one job description (Async)",
    tags=["analysis"],
)
async def analyze(
    payload: AnalysisRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    session_id: str | None = Depends(get_session_id),
) -> AnalysisResponse:
    resume = await db.get(Resume, payload.resume_id)
    if not resume or resume.session_id != session_id:
        raise HTTPException(status_code=404, detail="Resume not found.")

    job = await db.get(Job, payload.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    if resume.extraction_error and not (resume.cleaned_text or resume.raw_extracted_text):
        raise HTTPException(
            status_code=422,
            detail=f"Resume text extraction failed: {resume.extraction_error}",
        )

    # Create analysis record in queued status
    analysis = Analysis(
        resume_id=resume.id,
        job_id=job.id,
        status="STARTING",
        session_id=session_id,
    )
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)

    # Trigger background task
    from app.services.analyzer import process_analysis_task
    background_tasks.add_task(process_analysis_task, analysis.id)

    return AnalysisResponse.model_validate(analysis)


@router.get(
    "/analyses/{analysis_id}",
    response_model=AnalysisResponse,
    summary="Get analysis status and result",
    tags=["analysis"],
)
async def get_analysis(
    analysis_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    session_id: str | None = Depends(get_session_id),
) -> AnalysisResponse:
    analysis = await db.get(Analysis, analysis_id)
    if not analysis or analysis.session_id != session_id:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    return AnalysisResponse.model_validate(analysis)



@router.post(
    "/jobs/{job_id}/rank",
    response_model=RankResponse,
    summary="Rank multiple resumes against a job description",
    tags=["analysis"],
)
async def rank(
    job_id: uuid.UUID,
    payload: RankRequest,
    db: AsyncSession = Depends(get_db),
    session_id: str | None = Depends(get_session_id),
) -> RankResponse:
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    # Validate all requested resumes belong to the session
    if payload.resume_ids:
        stmt = select(func.count()).select_from(Resume).where(
            Resume.id.in_(payload.resume_ids),
            Resume.session_id == session_id
        )
        count = await db.scalar(stmt)
        if count != len(payload.resume_ids):
             raise HTTPException(status_code=403, detail="One or more resumes do not belong to this session.")

    try:
        analyses = await rank_resumes(db, job, payload.resume_ids)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Ranking failed: {e}")

    # Load resume filenames
    ranked_items: list[RankItem] = []
    for analysis in analyses:
        resume = await db.get(Resume, analysis.resume_id)
        ranked_items.append(
            RankItem(
                resume_id=analysis.resume_id,
                original_filename=resume.original_filename if resume else "Unknown",
                match_score_percent=analysis.match_score_percent,
                matching_skills=analysis.matching_skills,
                missing_skills_count=len(analysis.missing_skills),
                explanation=analysis.explanation,
                analysis_id=analysis.id,
            )
        )

    return RankResponse(job_id=job_id, ranked=ranked_items)


@router.post(
    "/compare",
    response_model=CompareResponse,
    summary="Compare multiple resumes side-by-side against a job description",
    tags=["analysis"],
)
async def compare(
    payload: CompareRequest,
    db: AsyncSession = Depends(get_db),
    session_id: str | None = Depends(get_session_id),
) -> CompareResponse:
    job = await db.get(Job, payload.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    # Validate all requested resumes belong to the session
    if payload.resume_ids:
        stmt = select(func.count()).select_from(Resume).where(
            Resume.id.in_(payload.resume_ids),
            Resume.session_id == session_id
        )
        count = await db.scalar(stmt)
        if count != len(payload.resume_ids):
             raise HTTPException(status_code=403, detail="One or more resumes do not belong to this session.")

    analyses = await rank_resumes(db, job, payload.resume_ids)
    return CompareResponse(
        job_id=payload.job_id,
        comparisons=[AnalysisResponse.model_validate(a) for a in analyses],
    )
