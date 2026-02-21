from __future__ import annotations


def build_explanation(
    matching_skills: list[str],
    missing_skills: list[str],
    match_score: float,
    sections: dict[str, str],
    jd_text: str,
) -> str:
    """
    Build an evidence-based explanation for the match score.
    Template-based, grounded in extracted skills and sections.
    No LLM required.
    """
    lines: list[str] = []

    # Score summary
    if match_score >= 75:
        lines.append(
            f"Strong match ({match_score:.1f}%): The resume aligns well with the job description."
        )
    elif match_score >= 50:
        lines.append(
            f"Moderate match ({match_score:.1f}%): The resume partially aligns with the job description."
        )
    else:
        lines.append(
            f"Weak match ({match_score:.1f}%): The resume has limited alignment with the job description."
        )

    # Matching skills evidence
    if matching_skills:
        top_matches = matching_skills[:8]
        lines.append(
            f"Matching skills found in resume: {', '.join(top_matches)}"
            + (f" (and {len(matching_skills) - 8} more)" if len(matching_skills) > 8 else ".")
        )
    else:
        lines.append("No matching skills were identified between the resume and job description.")

    # Missing skills evidence
    if missing_skills:
        top_missing = missing_skills[:5]
        lines.append(
            f"Key skills from JD not found in resume: {', '.join(top_missing)}"
            + (f" (and {len(missing_skills) - 5} more)" if len(missing_skills) > 5 else ".")
        )

    # Section evidence
    relevant_sections = [s for s in ["experience", "skills", "projects"] if s in sections]
    if relevant_sections:
        lines.append(f"Relevant sections detected: {', '.join(relevant_sections)}.")

    return " ".join(lines)


def build_suggestions(
    missing_skills: list[str],
    sections: dict[str, str],
    match_score: float,
) -> list[str]:
    """
    Generate actionable, grounded improvement suggestions.
    Based on missing skills and section analysis.
    """
    suggestions: list[str] = []

    if missing_skills:
        top_missing = missing_skills[:5]
        suggestions.append(
            f"Add or highlight these skills if you have experience with them: {', '.join(top_missing)}."
        )

    if "summary" not in sections and "header" in sections:
        suggestions.append(
            "Consider adding a professional summary section that highlights your key qualifications."
        )

    if "projects" not in sections and match_score < 70:
        suggestions.append(
            "Adding a Projects section with relevant work can improve your match score."
        )

    if "certifications" not in sections and any(
        kw in " ".join(missing_skills).lower()
        for kw in ["aws", "azure", "gcp", "certified", "pmp", "scrum"]
    ):
        suggestions.append(
            "Consider obtaining relevant certifications mentioned in the job description."
        )

    if match_score < 50:
        suggestions.append(
            "The overall semantic similarity is low. Review the job description carefully and "
            "tailor your resume language to better reflect the role's requirements."
        )

    if not suggestions:
        suggestions.append(
            "Your resume is a strong match. Ensure your experience descriptions use action verbs "
            "and quantify achievements where possible."
        )

    return suggestions
