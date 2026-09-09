from ai_analyzer import analyze_resume


sample_resume = """
John Doe

Skills:
Java, Python, SQL, HTML, CSS, JavaScript

Education:
Master of Computer Applications

Projects:
AI Resume Analyzer using Python and FastAPI.

Experience:
Fresher.
"""


result = analyze_resume(sample_resume)

print("\n--- GEMINI RESPONSE ---")
print(result)

print("\n--- SCORE ---")
print(result.score)

print("\n--- STRENGTHS ---")
print(result.strengths)

print("\n--- SUGGESTIONS ---")
print(result.suggestions)