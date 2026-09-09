import os
from typing import Dict, List

from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel, Field


load_dotenv()


class ResumeAnalysis(BaseModel):
    score: int = Field(ge=0, le=100)
    profile_summary: str
    strengths: List[str]
    areas_for_improvement: List[str]
    missing_skills_or_sections: List[str]
    suggestions: List[str]
    # JD matching fields — only populated when a job description is provided
    jd_match_score: int = Field(default=0, ge=0, le=100)
    matched_keywords: List[str] = Field(default_factory=list)
    missing_jd_keywords: List[str] = Field(default_factory=list)
    # Section-wise scoring — scores for each resume section (0-100)
    section_scores: Dict[str, int] = Field(default_factory=dict)
    # Section-wise improvement suggestions — keyed by section name
    section_suggestions: Dict[str, str] = Field(default_factory=dict)
    # ATS-friendly feedback — list of issues that could cause ATS rejection
    ats_issues: List[str] = Field(default_factory=list)


api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)


def analyze_resume(resume_text, job_description: str = None):

    # Build the JD section of the prompt only when a JD is provided
    if job_description and job_description.strip():
        jd_section = f"""
8. JOB DESCRIPTION MATCHING (a job description was provided):
   - jd_match_score (0-100): overall percentage match between the resume and the job requirements.
     Base this on how many required skills, tools, qualifications, and responsibilities
     from the JD are present in the resume.
   - matched_keywords: list every skill, tool, technology, qualification, or phrase that
     appears in BOTH the resume and the JD. Be thorough — include soft skills and domain terms.
   - missing_jd_keywords: list important skills, tools, technologies, or qualifications
     mentioned in the JD that are NOT found anywhere in the resume.

   Job Description:
   {job_description}
"""
    else:
        jd_section = """
8. JOB DESCRIPTION MATCHING (no job description provided):
   - Set jd_match_score to 0.
   - Set matched_keywords to an empty list [].
   - Set missing_jd_keywords to an empty list [].
"""

    prompt = f"""
You are an expert resume reviewer and career coach. Analyze the resume below and return
a structured JSON response following the output schema exactly.

═══════════════════════════════════════
GROUND RULES — READ BEFORE ANALYZING
═══════════════════════════════════════
1. Analyze ONLY the information present in the resume. Do NOT invent, assume, or
   hallucinate any skills, experience, education, certifications, or achievements.
2. Be honest and realistic. Do not inflate scores. A weak resume should score low.
3. Be specific and actionable. Vague feedback like "improve your resume" is not useful.
   Every suggestion must reference a concrete change the candidate can make.
4. Every required list field must contain at least one item.
5. Every required string field must be non-empty.
6. Use plain English. Avoid jargon unless it is present in the resume itself.

═══════════════════════════════════════
OUTPUT INSTRUCTIONS
═══════════════════════════════════════
1. OVERALL SCORE (score, 0-100):
   Score the resume holistically. Consider completeness, clarity, impact of content,
   formatting signals (inferred from text), and relevance.
   - 80-100: Excellent, ready to submit with minor polish
   - 60-79:  Good, a few clear gaps
   - 40-59:  Average, significant improvements needed
   - 0-39:   Weak, major restructuring required

2. PROFILE SUMMARY (profile_summary):
   Write 2-3 sentences summarising the candidate's background, level, and key skills
   based strictly on what is in the resume.

3. STRENGTHS (strengths):
   List 3-5 specific strengths evident in the resume. Reference actual content
   (e.g. "Has 2 internships in backend development", not "Has experience").

4. AREAS FOR IMPROVEMENT (areas_for_improvement):
   List 3-5 concrete weaknesses. Be direct. Reference what is missing or weak
   (e.g. "Work experience section lacks quantified achievements").

5. MISSING SKILLS OR SECTIONS (missing_skills_or_sections):
   List skills, tools, or resume sections that are absent but would strengthen the resume
   (e.g. "No LinkedIn URL", "Missing a Projects section", "No mention of version control").

6. SUGGESTIONS (suggestions):
   List 4-6 specific, prioritised action items the candidate should take to improve
   their resume before submitting. Each suggestion must be a complete sentence.

7. SECTION SCORING (section_scores, section_suggestions):
   - Identify every section present in the resume
     (e.g. Contact, Summary, Education, Experience, Skills, Projects,
      Certifications, Achievements, Languages, Interests).
   - Score each section 0-100 in section_scores using the section name as the key.
     Score based on completeness, clarity, and impact of that section alone.
   - For each section, write one specific improvement suggestion in section_suggestions
     using the exact same key. The suggestion must be actionable and section-specific.
   - Only include sections that actually exist in the resume.

{jd_section}
9. ATS-FRIENDLY FEEDBACK (ats_issues):
   ATS (Applicant Tracking Systems) are used by most employers to filter resumes before
   a human ever reads them. Check the resume text for the following common ATS problems
   and list each issue found as a clear, actionable sentence in ats_issues:
   - Missing contact information (no email, phone, or location)
   - No LinkedIn URL or GitHub/portfolio link
   - Using non-standard section headings (e.g. "My Journey" instead of "Experience")
   - Lack of measurable achievements or metrics in experience bullets
   - Very short resume (under-detailed, likely to score low in ATS ranking)
   - Excessive use of personal pronouns (I, me, my) — ATS prefers noun-led bullets
   - No mention of relevant tools, technologies, or keywords (especially for tech roles)
   - Dates missing or in non-standard format in experience/education sections
   - Only one page but 5+ years of experience listed (or vice versa)
   - Missing a Skills section
   If none of these issues are found, set ats_issues to an empty list [].
   Do NOT invent issues — only flag problems that are clearly evident from the resume text.

═══════════════════════════════════════
RESUME TEXT
═══════════════════════════════════════
{resume_text}
"""

    interaction = client.interactions.create(
        model="gemini-3.6-flash",
        input=prompt,
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": ResumeAnalysis.model_json_schema()
        }
    )

    analysis = ResumeAnalysis.model_validate_json(
        interaction.output_text
    )

    return analysis