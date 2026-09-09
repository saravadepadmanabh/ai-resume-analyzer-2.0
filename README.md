# AI Resume Analyzer

An AI-powered web application that analyzes a resume and gives structured, actionable feedback — including a score, section-wise breakdown, ATS compatibility check, and optional job description matching.

Upload a PDF or DOCX resume, optionally paste a job description, and get a full analysis in seconds.

---

## What It Does

- Extracts text from PDF and DOCX resumes (including tables and text boxes)
- Sends the text to Google Gemini AI with a structured prompt
- Returns and displays:
  - **Overall resume score** (0–100)
  - **Candidate profile summary**
  - **Key strengths**
  - **Areas for improvement**
  - **Missing skills or sections**
  - **Improvement suggestions**
  - **Section-wise scores** with progress bars (Contact, Education, Experience, Skills, etc.)
  - **Section improvement suggestions** — one actionable tip per section
  - **ATS compatibility issues** — flags things that could cause rejection by applicant tracking systems
  - **Job description match score** (when a JD is pasted)
  - **Matched keywords** — skills present in both the resume and the JD
  - **Missing JD keywords** — important skills in the JD that are absent from the resume
- Highlights matched keywords in the profile summary and suggestions
- Downloadable analysis report (browser print / save as PDF)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript (no frameworks) |
| Backend | Python, FastAPI, Uvicorn |
| PDF extraction | PyMuPDF |
| DOCX extraction | python-docx |
| AI | Google Gemini API via google-genai SDK |
| Validation | Pydantic v2 + custom validator |

---

## Project Structure

```
ai-resume-analyzer/
│
├── backend/
│   ├── main.py          # FastAPI app — routes and request handling
│   ├── ai_analyzer.py   # Gemini integration, prompt, ResumeAnalysis model
│   ├── validator.py     # Post-AI response validation
│   ├── pdf_parser.py    # PDF text extraction (PyMuPDF)
│   ├── docx_parser.py   # DOCX text extraction (paragraphs + tables + text boxes)
│   └── requirements.txt
│
├── fronend/
│   ├── index.html       # Upload screen + results dashboard
│   ├── style.css        # All styles including print stylesheet
│   └── script.js        # File validation, API call, dashboard rendering
│
├── .env                 # GEMINI_API_KEY (not committed)
├── .gitignore
└── README.md
```

---

## Setup and Installation

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd "ai-resume-analyzer - 2.0"
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
```

**Windows:**
```bash
venv\Scripts\activate
```

**Mac / Linux:**
```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r backend/requirements.txt
```

### 4. Set up the Gemini API key

Create a `.env` file in the project root:

```
GEMINI_API_KEY=your_api_key_here
```

Get a free API key at [aistudio.google.com](https://aistudio.google.com).
The `.env` file is excluded from Git via `.gitignore`.

### 5. Start the backend

```bash
uvicorn backend.main:app --reload
```

The backend runs at `http://127.0.0.1:8000`.
You can verify it by visiting that URL — it should return:
```json
{"message": "AI Resume Analyzer backend is running"}
```

### 6. Open the frontend

Double-click `fronend/index.html` or open it in your browser directly.
No web server needed — it connects to the backend at `localhost:8000`.

---

## How to Use

1. Open `index.html` in your browser
2. Click **Choose your resume** and select a PDF or DOCX file
3. Optionally paste a job description into the text area
4. Click **Analyze Resume**
5. Wait for the analysis (usually 5–15 seconds)
6. Review the dashboard:
   - Score rings at the top
   - Section score bars
   - Two-column card grid with all feedback
   - ATS warning banner (if issues are found)
7. Click **Download Report** to save as PDF
8. Click **Analyze Another** to go back and analyze a different resume

---

## Architecture and Flow

```
Browser (index.html + script.js)
        |
        |  POST /upload
        |  multipart/form-data: file + optional job_description
        ↓
FastAPI (main.py)
        |
        ├── Validate file type (PDF / DOCX only)
        ├── Extract text
        │     ├── PDF  → pdf_parser.py  (PyMuPDF)
        │     └── DOCX → docx_parser.py (paragraphs + tables + text boxes)
        |
        ├── Send text + optional JD to Gemini AI
        │     └── ai_analyzer.py
        |
        ├── Parse and validate AI response
        │     ├── Pydantic model (ResumeAnalysis)
        │     └── validator.py (non-empty checks, score range, field types)
        |
        └── Return JSON response
                |
                ↓
        script.js populates dashboard
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Health check |
| POST | `/upload` | Upload resume, get analysis |

**POST `/upload` — request:**
- `file` (required): PDF or DOCX resume file
- `job_description` (optional): plain text job description

**POST `/upload` — success response:**
```json
{
  "success": true,
  "filename": "resume.pdf",
  "jd_provided": false,
  "analysis": {
    "score": 74,
    "profile_summary": "...",
    "strengths": ["..."],
    "areas_for_improvement": ["..."],
    "missing_skills_or_sections": ["..."],
    "suggestions": ["..."],
    "section_scores": { "Education": 80, "Skills": 65 },
    "section_suggestions": { "Education": "Add GPA or relevant coursework." },
    "ats_issues": ["No LinkedIn URL found.", "..."],
    "jd_match_score": 0,
    "matched_keywords": [],
    "missing_jd_keywords": []
  }
}
```

---

## AI Integration

**Model:** Gemini 3.6 Flash via the `google-genai` Python SDK

**How structured output works:**
The prompt instructs Gemini to return a JSON object. The `response_format` parameter passes the exact JSON schema derived from the `ResumeAnalysis` Pydantic model — so Gemini is constrained to return only the expected fields in the expected types.

**Prompt design:**
The prompt is broken into clearly numbered sections with explicit rules:

1. Ground rules — analyze only what's in the resume, never invent information
2. Overall score — with a scoring rubric (0–39 weak, 40–59 average, 60–79 good, 80–100 excellent)
3. Profile summary — 2–3 sentences based only on resume content
4. Strengths — 3–5 specific, referencing actual resume content
5. Areas for improvement — concrete, not vague
6. Missing skills/sections — what's absent but would strengthen the resume
7. Suggestions — 4–6 prioritized action items
8. Section scoring — identify present sections, score each, give one tip per section
9. ATS feedback — check for 10 specific ATS problems
10. JD matching — (only when JD provided) match score, matched keywords, missing keywords

**Validation:**
After Pydantic parses the response, a second pass in `validator.py` checks:
- Required lists are non-empty and contain only non-empty strings
- `profile_summary` is not blank
- `score` and `jd_match_score` are between 0 and 100
- `section_scores` values are valid integers
- `ats_issues` items are non-empty strings (empty list is valid — no issues found)

---

## Error Handling

| Scenario | Response |
|---|---|
| No file selected | Inline error banner in the UI |
| Wrong file type (client-side) | Inline error banner before any network request |
| Wrong file type (server-side) | HTTP 400 |
| Unreadable / image-based file | HTTP 422 |
| Gemini rate limit / quota | HTTP 429 with user-friendly message |
| AI returns invalid structure | `success: false` with message |
| Backend not running | Network error caught, inline banner shown |

All errors show an inline banner in the UI — no browser `alert()` popups.

---

## DOCX Text Extraction

Most resume templates use tables for layout. The DOCX parser handles:
- **Paragraphs** — standard body text and headings
- **Tables** — all rows and cells, with nested table support
- **Text boxes and shapes** — extracted via XML namespace parsing (`wp:inline`, `wp:anchor` → `a:t` elements)

---

## Limitations

- Scanned or image-based PDFs cannot be read (no OCR support)
- Analysis quality depends on how much readable text the resume contains
- Requires an internet connection to reach the Gemini API
- Subject to Gemini API rate limits (free tier has per-minute limits)
- The frontend connects to `localhost:8000` — both must run on the same machine

---

## AI Tools Used During Development

- **ChatGPT** — used for initial project planning, understanding the overall approach, guidance on project structure, basic feature development, and general coding help during the early stages of the project
- **Kiro AI** — used for feature additions, iterative improvements, debugging, and refining the implementation as the project grew
- **Google Gemini** — the AI model used at runtime for resume analysis

All AI-generated code and suggestions were reviewed and tested before being accepted.

---

## Testing Checklist

| Test case | Expected result |
|---|---|
| Upload valid PDF | Analysis displayed |
| Upload valid DOCX | Analysis displayed |
| Upload DOCX with table-based layout | Text extracted correctly |
| No file selected | Error banner shown |
| Upload unsupported file (e.g. .txt) | Error banner shown |
| Upload with job description | JD match score + keywords shown |
| Upload without job description | JD section hidden |
| ATS issues present | Warning banner shown |
| No ATS issues | Banner hidden |
| Backend not running | "Could not connect" error banner |
| Gemini quota exceeded | Rate-limit error banner |
| Click Download Report | Browser print dialog opens |
| Click Analyze Another | Upload screen restored, form cleared |

## Live Demo

The latest version of the AI Resume Analyzer is deployed and available here:

**Live Application:**
https://ai-resume-analyzer-2-0-frontend.onrender.com/

> **Note:** The application uses the Gemini AI API for resume analysis. The Gemini API may have a limited number of requests depending on the available API quota. If the API quota/limit is exhausted and the application stops generating AI-based analysis, please contact **[padmanabhsaravade@gmail.com](mailto:padmanabhsaravade@gmail.com)** to request a new API key for further usage.



