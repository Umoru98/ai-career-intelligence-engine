from __future__ import annotations

import numpy as np

from app.core.config import get_settings

settings = get_settings()

# Lazy-loaded model
_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(settings.sentence_transformer_model)
    return _model


def _truncate_text(text: str, max_chars: int = 8000) -> str:
    """
    Truncate text to max_chars to avoid exceeding model token limits.
    Documented limit: ~512 tokens ≈ ~2000-4000 chars for MiniLM.
    We use 8000 chars as a safe upper bound (model handles truncation internally).
    """
    if len(text) > max_chars:
        return text[:max_chars] + "... [truncated]"
    return text


async def generate_embedding(text: str) -> list[float]:
    """
    Generate a sentence embedding for the given text asynchronously.
    Offloads the CPU-bound model.encode() call to a thread.
    Returns a list of floats (the embedding vector).
    """
    import asyncio

    model = _get_model()
    truncated = _truncate_text(text)
    
    # Run the heavy cpu-bound inference in a thread
    embedding = await asyncio.to_thread(model.encode, truncated, normalize_embeddings=True)
    return embedding.tolist()


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.
    Since we use normalize_embeddings=True, this is just a dot product.
    Returns value in [-1, 1].
    """
    a = np.array(vec_a, dtype=np.float32)
    b = np.array(vec_b, dtype=np.float32)
    dot = float(np.dot(a, b))
    norm_a = float(np.linalg.norm(a))
    norm_b = float(np.linalg.norm(b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def similarity_to_score(cos_sim: float) -> float:
    """
    Convert cosine similarity [-1, 1] to match score [0, 100].

    Mapping: score = clamp((cos_sim + 1) / 2 * 100, 0, 100)

    This is a linear mapping:
    - cos_sim = 1.0  → 100%
    - cos_sim = 0.0  → 50%
    - cos_sim = -1.0 → 0%

    For resume matching, typical values are 0.3–0.9.
    Documented: this is a linear normalization, not a calibrated threshold.
    TODO: calibrate with labeled data for better score distribution.
    """
    score = (cos_sim + 1.0) / 2.0 * 100.0
    return round(max(0.0, min(100.0, score)), 2)


async def compute_match_score(
    resume_text: str,
    jd_text: str,
    resume_embedding: list[float] | None = None,
    jd_embedding: list[float] | None = None,
) -> tuple[float, list[float], list[float]]:
    """
    Compute match score between resume and JD.
    Returns (score_percent, resume_embedding, jd_embedding).
    Generates embeddings if not provided asynchronously to avoid blocking.
    """
    if resume_embedding is None:
        resume_embedding = await generate_embedding(resume_text)
    if jd_embedding is None:
        jd_embedding = await generate_embedding(jd_text)

    cos_sim = cosine_similarity(resume_embedding, jd_embedding)
    score = similarity_to_score(cos_sim)
    return score, resume_embedding, jd_embedding
