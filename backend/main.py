from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

from backend.pdf_parser import extract_text_from_pdf
from backend.ai_analyzer import analyze_resume
from backend.validator import validate_analysis
from backend.docx_parser import extract_text_from_docx


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "message": "AI Resume Analyzer backend is running"
    }


@app.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    job_description: Optional[str] = Form(default=None)
):

    # Check file type
    if file.content_type not in [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are allowed."
        )
    try:

        # Read uploaded file
        file_bytes = await file.read()

        # Extract text
        if file.content_type == "application/pdf":
            resume_text = extract_text_from_pdf(file_bytes)
        else:
            resume_text = extract_text_from_docx(file_bytes)

        # Check whether text was extracted
        if not resume_text.strip():
            raise HTTPException(
                status_code=422,
                detail="Could not extract readable text from this File."
            )

        # Determine if a job description was supplied
        jd_provided = bool(job_description and job_description.strip())

        # Send resume text (and optional JD) to Gemini
        analysis = analyze_resume(resume_text, job_description)

        # Validate AI response
        if not validate_analysis(analysis, jd_provided=jd_provided):
            return {
                "success": False,
                "message": "AI returned an invalid analysis."
            }

        # Return successful analysis
        return {
            "success": True,
            "message": "Resume analyzed successfully.",
            "filename": file.filename,
            "jd_provided": jd_provided,
            "analysis": analysis.model_dump()
        }
    except HTTPException:
        raise

    except Exception as error:

        print("Error:", error)

        error_message = str(error).lower()

    # Check for Gemini quota or rate-limit errors
        if (
            "resource_exhausted" in error_message
            or "quota" in error_message
            or "rate limit" in error_message
            or "429" in error_message
         ):
            raise HTTPException(
                status_code=429,
                detail="Gemini API quota has been reached; please try again later."
            )

    # Other Gemini/API errors
        return {
            "success": False,
            "message": "The resume could not be processed. Please try again."
        }