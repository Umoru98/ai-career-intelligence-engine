from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Analysis, Embedding, Job, Resume
from app.services.embedder import compute_match_score
from app.services.explainer import build_explanation, build_suggestions
from app.services.nlp_pipeline import (
    compute_skill_overlap,
    detect_sections,
    extract_skills_from_text,
    load_skills_taxonomy,
)


async def run_analysis(
    db: AsyncSession,
    resume: Resume,
    job: Job,
) -> Analysis:
    """
    Full analysis pipeline for one resume vs one job description.
    Returns an Analysis ORM object (not yet committed).
    """
    skills_taxonomy = load_skills_taxonomy()

    # Use redacted_text for embeddings (bias-aware)
    resume_text = resume.redacted_text or resume.cleaned_text or resume.raw_extracted_text or ""
    jd_text = job.description

    if not resume_text.strip():
        raise ValueError(f"Resume {resume.id} has no extractable text.")

    # Check for existing embeddings
    resume_emb_row = await db.scalar(
        select(Embedding).where(
            Embedding.owner_id == resume.id,
            Embedding.owner_type == "resume",
        )
    )
    job_emb_row = await db.scalar(
        select(Embedding).where(
            Embedding.owner_id == job.id,
            Embedding.owner_type == "job",
        )
    )

    resume_vec = resume_emb_row.embedding_json if resume_emb_row else None
    job_vec = job_emb_row.embedding_json if job_emb_row else None

    # Compute match score (generates embeddings if not cached)
    score, resume_vec, job_vec = compute_match_score(resume_text, jd_text, resume_vec, job_vec)

    # Persist embeddings if not already stored
    from app.core.config import get_settings

    settings = get_settings()

    if not resume_emb_row:
        emb = Embedding(
            owner_type="resume",
            owner_id=resume.id,
            embedding_json=resume_vec,
            model_name=settings.sentence_transformer_model,
        )
        db.add(emb)

    if not job_emb_row:
        emb = Embedding(
            owner_type="job",
            owner_id=job.id,
            embedding_json=job_vec,
            model_name=settings.sentence_transformer_model,
        )
        db.add(emb)

    # Skills extraction
    resume_skills = extract_skills_from_text(resume_text, skills_taxonomy)
    jd_skills = extract_skills_from_text(jd_text, skills_taxonomy)
    matching_skills, missing_skills = compute_skill_overlap(resume_skills, jd_skills)

    # Section detection
    sections = resume.sections_json or detect_sections(resume_text)

    # Build section summary (first 200 chars of each section)
    section_summary = {
        name: content[:200] + ("..." if len(content) > 200 else "")
        for name, content in sections.items()
        if name not in ("header",)
    }

    # Build explanation and suggestions
    explanation = build_explanation(matching_skills, missing_skills, score, sections, jd_text)
    suggestions = build_suggestions(missing_skills, sections, score)

    # Create or update analysis
    analysis = Analysis(
        resume_id=resume.id,
        job_id=job.id,
        match_score_percent=score,
        matching_skills=matching_skills,
        missing_skills=missing_skills,
        section_summary=section_summary,
        explanation=explanation,
        suggestions=suggestions,
    )
    db.add(analysis)
    await db.flush()  # get the ID without committing

    return analysis


async def rank_resumes(
    db: AsyncSession,
    job: Job,
    resume_ids: list[uuid.UUID] | None = None,
) -> list[Analysis]:
    """
    Rank all (or selected) resumes against a job description.
    Returns analyses sorted by match_score_percent descending.
    """
    if resume_ids:
        stmt = select(Resume).where(Resume.id.in_(resume_ids))
    else:
        stmt = select(Resume)

    result = await db.execute(stmt)
    resumes = result.scalars().all()

    analyses: list[Analysis] = []
    for resume in resumes:
        # Check if analysis already exists
        existing = await db.scalar(
            select(Analysis).where(
                Analysis.resume_id == resume.id,
                Analysis.job_id == job.id,
            )
        )
        if existing:
            analyses.append(existing)
        else:
            try:
                analysis = await run_analysis(db, resume, job)
                analyses.append(analysis)
            except Exception as e:
                # Log and skip resumes that fail
                print(f"Warning: Analysis failed for resume {resume.id}: {e}")
                continue

    await db.commit()

    # Sort by score descending
    analyses.sort(key=lambda a: a.match_score_percent, reverse=True)
    return analyses
