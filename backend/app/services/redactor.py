from __future__ import annotations

import re

# Lazy-loaded spaCy model
_nlp = None


def _get_nlp():
    global _nlp
    if _nlp is None:
        import spacy

        from app.core.config import get_settings

        settings = get_settings()
        try:
            _nlp = spacy.load(settings.spacy_model)
        except OSError:
            # Fallback: blank English model if the full model isn't downloaded
            _nlp = spacy.blank("en")
    return _nlp


# Regex patterns for PII
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")
_PHONE_RE = re.compile(r"(\+?\d[\d\s\-\(\)\.]{7,}\d)")
_URL_RE = re.compile(r"https?://\S+|www\.\S+")
_ADDRESS_RE = re.compile(
    r"\b\d{1,5}\s+[A-Za-z\s]{3,40}(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Way|Place|Pl)\b",
    re.IGNORECASE,
)
_DOB_RE = re.compile(
    r"\b(?:Date\s+of\s+Birth|DOB|Born\s+on)[:\s]+\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}\b",
    re.IGNORECASE,
)
_LINKEDIN_RE = re.compile(r"linkedin\.com/in/[\w\-]+", re.IGNORECASE)
_GITHUB_RE = re.compile(r"github\.com/[\w\-]+", re.IGNORECASE)


def redact_text(text: str) -> str:
    """
    Remove PII-like fields from resume text:
    - PERSON entities (via spaCy NER)
    - Emails, phone numbers, URLs, addresses, DOB
    - LinkedIn/GitHub profile URLs (keep platform name, remove username)

    Keeps job-relevant content (skills, roles, responsibilities, tools).
    """
    nlp = _get_nlp()

    # spaCy NER for PERSON entities
    # Process in chunks to handle long texts
    MAX_CHARS = 100_000
    truncated = text[:MAX_CHARS]
    doc = nlp(truncated)

    redacted = truncated
    # Replace PERSON entities (reverse order to preserve offsets)
    person_spans = [(ent.start_char, ent.end_char) for ent in doc.ents if ent.label_ == "PERSON"]
    for start, end in reversed(person_spans):
        redacted = redacted[:start] + "[NAME]" + redacted[end:]

    # Regex-based PII removal
    redacted = _EMAIL_RE.sub("[EMAIL]", redacted)
    redacted = _PHONE_RE.sub("[PHONE]", redacted)
    redacted = _DOB_RE.sub("[DOB REDACTED]", redacted)
    redacted = _ADDRESS_RE.sub("[ADDRESS]", redacted)
    redacted = _LINKEDIN_RE.sub("linkedin.com/in/[PROFILE]", redacted)
    redacted = _GITHUB_RE.sub("github.com/[PROFILE]", redacted)
    # Remove remaining URLs (may contain usernames)
    redacted = _URL_RE.sub("[URL]", redacted)

    # If text was truncated, append the rest (unredacted but beyond NER range)
    if len(text) > MAX_CHARS:
        remainder = text[MAX_CHARS:]
        remainder = _EMAIL_RE.sub("[EMAIL]", remainder)
        remainder = _PHONE_RE.sub("[PHONE]", remainder)
        redacted = redacted + remainder

    return redacted
