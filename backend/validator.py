from backend.ai_analyzer import ResumeAnalysis


def _is_non_empty_string_list(value):
    """Check that a value is a list with at least one non-empty string item."""
    if not isinstance(value, list):
        return False
    if len(value) == 0:
        return False
    for item in value:
        if not isinstance(item, str) or not item.strip():
            return False
    return True


def validate_analysis(analysis, jd_provided: bool = False):

    if not isinstance(analysis, ResumeAnalysis):
        return False

    if not 0 <= analysis.score <= 100:
        return False

    if not analysis.profile_summary or not analysis.profile_summary.strip():
        return False

    # Each of these lists must have at least one real string item
    if not _is_non_empty_string_list(analysis.strengths):
        return False

    if not _is_non_empty_string_list(analysis.areas_for_improvement):
        return False

    if not _is_non_empty_string_list(analysis.missing_skills_or_sections):
        return False

    if not _is_non_empty_string_list(analysis.suggestions):
        return False

    # Validate JD fields only when a job description was provided
    if jd_provided:
        if not 0 <= analysis.jd_match_score <= 100:
            return False

        # matched_keywords and missing_jd_keywords can be empty lists (valid when
        # there are no matches / no gaps), but items must be non-empty strings
        if not isinstance(analysis.matched_keywords, list):
            return False
        for item in analysis.matched_keywords:
            if not isinstance(item, str) or not item.strip():
                return False

        if not isinstance(analysis.missing_jd_keywords, list):
            return False
        for item in analysis.missing_jd_keywords:
            if not isinstance(item, str) or not item.strip():
                return False

    # Validate section_scores — must be a dict with string keys and int values 0-100
    if not isinstance(analysis.section_scores, dict):
        return False
    for section, score in analysis.section_scores.items():
        if not isinstance(section, str) or not section.strip():
            return False
        if not isinstance(score, int) or not 0 <= score <= 100:
            return False

    # Validate section_suggestions — must be a dict with string keys and non-empty string values
    if not isinstance(analysis.section_suggestions, dict):
        return False
    for section, suggestion in analysis.section_suggestions.items():
        if not isinstance(section, str) or not section.strip():
            return False
        if not isinstance(suggestion, str) or not suggestion.strip():
            return False

    # Validate ats_issues — can be empty (no issues found is valid),
    # but if populated, every item must be a non-empty string
    if not isinstance(analysis.ats_issues, list):
        return False
    for item in analysis.ats_issues:
        if not isinstance(item, str) or not item.strip():
            return False

    return True