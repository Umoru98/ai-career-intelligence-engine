from __future__ import annotations

import re
from pathlib import Path

import yaml

# ── Section Detection ──────────────────────────────────────────────────────────

SECTION_PATTERNS: dict[str, re.Pattern] = {
    "contact": re.compile(
        r"^(?:contact|personal\s+information|contact\s+information|contact\s+details)\s*$",
        re.IGNORECASE | re.MULTILINE,
    ),
    "summary": re.compile(
        r"^(?:summary|professional\s+summary|objective|profile|about\s+me|career\s+objective)\s*$",
        re.IGNORECASE | re.MULTILINE,
    ),
    "experience": re.compile(
        r"^(?:experience|work\s+experience|professional\s+experience|employment|employment\s+history|work\s+history|career\s+history)\s*$",
        re.IGNORECASE | re.MULTILINE,
    ),
    "education": re.compile(
        r"^(?:education|academic\s+background|educational\s+background|qualifications|academic\s+qualifications)\s*$",
        re.IGNORECASE | re.MULTILINE,
    ),
    "skills": re.compile(
        r"^(?:skills|technical\s+skills|core\s+competencies|competencies|key\s+skills|skill\s+set|technologies|tech\s+stack)\s*$",
        re.IGNORECASE | re.MULTILINE,
    ),
    "projects": re.compile(
        r"^(?:projects|personal\s+projects|key\s+projects|notable\s+projects|portfolio)\s*$",
        re.IGNORECASE | re.MULTILINE,
    ),
    "certifications": re.compile(
        r"^(?:certifications?|certificates?|licenses?|accreditations?|credentials?)\s*$",
        re.IGNORECASE | re.MULTILINE,
    ),
    "awards": re.compile(
        r"^(?:awards?|honors?|achievements?|accomplishments?|recognition)\s*$",
        re.IGNORECASE | re.MULTILINE,
    ),
    "publications": re.compile(
        r"^(?:publications?|research|papers?|articles?)\s*$",
        re.IGNORECASE | re.MULTILINE,
    ),
    "languages": re.compile(
        r"^(?:languages?|language\s+proficiency)\s*$",
        re.IGNORECASE | re.MULTILINE,
    ),
    "interests": re.compile(
        r"^(?:interests?|hobbies|activities|volunteer|volunteering)\s*$",
        re.IGNORECASE | re.MULTILINE,
    ),
    "references": re.compile(
        r"^(?:references?|referees?)\s*$",
        re.IGNORECASE | re.MULTILINE,
    ),
}


def detect_sections(text: str) -> dict[str, str]:
    """
    Split resume text into named sections using heading regex rules.
    Falls back to 'unknown' for unmatched content.

    Returns: {section_name: text_content}
    """
    lines = text.split("\n")
    sections: dict[str, list[str]] = {}
    current_section = "header"
    sections[current_section] = []

    for line in lines:
        stripped = line.strip()
        matched_section = None

        for section_name, pattern in SECTION_PATTERNS.items():
            if pattern.match(stripped):
                matched_section = section_name
                break

        if matched_section:
            current_section = matched_section
            if current_section not in sections:
                sections[current_section] = []
        else:
            sections[current_section].append(line)

    # Convert lists to strings, filter empty sections
    result: dict[str, str] = {}
    for name, lines_list in sections.items():
        content = "\n".join(lines_list).strip()
        if content:
            result[name] = content

    return result


# ── Skills Extraction ──────────────────────────────────────────────────────────

_skills_cache: list[str] | None = None


def load_skills_taxonomy() -> list[str]:
    """Load skills from skills.yml, cached after first load."""
    global _skills_cache
    if _skills_cache is not None:
        return _skills_cache

    skills_path = Path(__file__).parent.parent / "data" / "skills.yml"
    if skills_path.exists():
        with open(skills_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
            all_skills: list[str] = []
            if isinstance(data, dict):
                for category_skills in data.values():
                    if isinstance(category_skills, list):
                        all_skills.extend(category_skills)
            elif isinstance(data, list):
                all_skills = data
            _skills_cache = [s.lower().strip() for s in all_skills if s]
    else:
        _skills_cache = []

    return _skills_cache


def extract_skills_from_text(text: str, skills_taxonomy: list[str] | None = None) -> list[str]:
    """
    Extract skills from text using dictionary/phrase matching.
    Case-insensitive, word-boundary aware.
    Returns sorted list of matched skills (original casing from taxonomy).
    """
    if skills_taxonomy is None:
        skills_taxonomy = load_skills_taxonomy()

    text_lower = text.lower()
    found: list[str] = []

    for skill in skills_taxonomy:
        # Word-boundary aware matching
        pattern = r"(?<![a-zA-Z0-9\-_])" + re.escape(skill) + r"(?![a-zA-Z0-9\-_])"
        if re.search(pattern, text_lower):
            found.append(skill)

    return sorted(set(found))


def compute_skill_overlap(
    resume_skills: list[str], jd_skills: list[str]
) -> tuple[list[str], list[str]]:
    """
    Returns (matching_skills, missing_skills).
    matching = intersection(resume, jd)
    missing = jd - resume
    """
    resume_set = set(resume_skills)
    jd_set = set(jd_skills)
    matching = sorted(resume_set & jd_set)
    missing = sorted(jd_set - resume_set)
    return matching, missing
