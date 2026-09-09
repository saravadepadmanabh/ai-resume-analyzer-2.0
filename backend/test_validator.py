from ai_analyzer import ResumeAnalysis
from validator import validate_analysis


valid_analysis = ResumeAnalysis(
    score=80,
    profile_summary="A fresher with programming skills.",
    strengths=["Java", "Python"],
    areas_for_improvement=["Add more project details"],
    missing_skills_or_sections=["Certifications"],
    suggestions=["Add measurable project achievements"]
)


result = validate_analysis(valid_analysis)

print("Validation result:", result)