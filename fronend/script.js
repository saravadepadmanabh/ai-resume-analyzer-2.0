// ── Element references ────────────────────────────────────────────
const uploadScreen      = document.getElementById("uploadScreen");
const dashboard         = document.getElementById("dashboard");
const loading           = document.getElementById("loading");
const resumeInput       = document.getElementById("resume");
const analyzeButton     = document.getElementById("analyzeButton");
const jobDescriptionInput = document.getElementById("jobDescription");
const errorBox          = document.getElementById("errorBox");
const errorMessage      = document.getElementById("errorMessage");
const errorClose        = document.getElementById("errorClose");
const analyzeAnotherBtn = document.getElementById("analyzeAnotherBtn");

// ── Helpers ───────────────────────────────────────────────────────

// Escape special regex characters
function escapeRegex(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

// Wrap matched keywords in <mark> — longest first to avoid partial matches
function highlightKeywords(text, keywords) {
  if (!keywords || keywords.length === 0) return text;
  const sorted = [...keywords].sort((a, b) => b.length - a.length);
  let result = text;
  sorted.forEach(function (kw) {
    const pattern = new RegExp("(" + escapeRegex(kw) + ")", "gi");
    result = result.replace(pattern, '<mark class="kw-highlight">$1</mark>');
  });
  return result;
}

// Show inline error banner
function showError(message) {
  errorMessage.textContent = message;
  errorBox.style.display = "flex";
  errorBox.scrollIntoView({ behavior: "smooth", block: "center" });
}

// Hide inline error banner
function hideError() {
  errorBox.style.display = "none";
  errorMessage.textContent = "";
}

// Populate a <ul> with plain text items
function fillList(ulId, items) {
  const ul = document.getElementById(ulId);
  ul.innerHTML = "";
  items.forEach(function (item) {
    const li = document.createElement("li");
    li.textContent = item;
    ul.appendChild(li);
  });
}

// Populate a <ul> with items that may contain highlighted HTML
function fillListHtml(ulId, items) {
  const ul = document.getElementById(ulId);
  ul.innerHTML = "";
  items.forEach(function (item) {
    const li = document.createElement("li");
    li.innerHTML = item;
    ul.appendChild(li);
  });
}

// Animate an SVG ring fill using stroke-dashoffset
// circumference for r=52 is 2π×52 ≈ 326.73
function animateRing(ringId, score) {
  const circumference = 326.73;
  const ring = document.getElementById(ringId);
  if (!ring) return;
  const offset = circumference - (score / 100) * circumference;
  // Small delay so the CSS transition fires after the element is visible
  setTimeout(function () {
    ring.style.strokeDashoffset = offset;
  }, 80);
}

// ── Reset — go back to upload screen ─────────────────────────────
function resetToUpload() {
  dashboard.style.display = "none";
  uploadScreen.style.display = "flex";

  // Clear file input and JD textarea
  resumeInput.value = "";
  jobDescriptionInput.value = "";

  // Reset rings so they are empty on next run
  const scoreRing = document.getElementById("scoreRingFill");
  const jdRing    = document.getElementById("jdRingFill");
  if (scoreRing) scoreRing.style.strokeDashoffset = "326.73";
  if (jdRing)    jdRing.style.strokeDashoffset    = "326.73";

  hideError();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

// Wire "Analyze Another" button
errorClose.addEventListener("click", hideError);
analyzeAnotherBtn.addEventListener("click", resetToUpload);

// ── Main analyze handler ──────────────────────────────────────────
analyzeButton.addEventListener("click", async function () {

  hideError();

  // Validate file selected
  if (resumeInput.files.length === 0) {
    showError("Please select a PDF or DOCX file before analyzing.");
    return;
  }

  const resumeFile = resumeInput.files[0];

  // Validate file type
  if (
    resumeFile.type !== "application/pdf" &&
    resumeFile.type !== "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
  ) {
    showError("Only PDF and DOCX files are supported. Please choose a valid file.");
    return;
  }

  // Build form data
  const formData = new FormData();
  formData.append("file", resumeFile);

  const jobDescription = jobDescriptionInput.value.trim();
  if (jobDescription) {
    formData.append("job_description", jobDescription);
  }

  // Show loading overlay
  loading.style.display = "flex";

  try {
    const response = await fetch("https://ai-resume-analyzer-2-0.onrender.com/upload", {
      method: "POST",
      body: formData,
    });

    const result = await response.json();
    console.log(result);

    // ── HTTP error handling ───────────────────────────────────────
    if (!response.ok) {
      if (response.status === 429) {
        showError("The AI service is rate-limited. Please wait a moment and try again.");
      } else if (response.status === 422) {
        showError("Could not extract text from this file. Make sure it is not a scanned image.");
      } else if (response.status === 400) {
        showError(result.detail || "Invalid file type. Only PDF and DOCX are allowed.");
      } else {
        showError(result.detail || "Something went wrong. Please try again.");
      }
      return;
    }

    // ── Application-level failure ─────────────────────────────────
    if (!result.success) {
      showError(result.message || "The AI could not process this resume. Please try again.");
      return;
    }

    const analysis = result.analysis;

    // Keywords for highlighting (only when JD was provided)
    const keywords = (result.jd_provided && analysis.matched_keywords)
      ? analysis.matched_keywords : [];

    // ── Top bar filename ──────────────────────────────────────────
    document.getElementById("dashFilename").textContent = result.filename || resumeFile.name;

    // ── Overall score ring ────────────────────────────────────────
    document.getElementById("score").textContent = analysis.score;
    animateRing("scoreRingFill", analysis.score);

    // ── Profile summary ───────────────────────────────────────────
    const profileEl = document.getElementById("profileSummary");
    if (keywords.length > 0) {
      profileEl.innerHTML = highlightKeywords(analysis.profile_summary, keywords);
    } else {
      profileEl.textContent = analysis.profile_summary;
    }

    // ── Strengths ─────────────────────────────────────────────────
    fillList("strengths", analysis.strengths);

    // ── Areas for improvement ─────────────────────────────────────
    fillList("improvements", analysis.areas_for_improvement);

    // ── Missing skills / sections ─────────────────────────────────
    fillList("missing", analysis.missing_skills_or_sections);

    // ── Suggestions (with keyword highlighting) ───────────────────
    if (keywords.length > 0) {
      fillListHtml("suggestions", analysis.suggestions.map(function (s) {
        return highlightKeywords(s, keywords);
      }));
    } else {
      fillList("suggestions", analysis.suggestions);
    }

    // ── JD match ──────────────────────────────────────────────────
    const jdHeroCard      = document.getElementById("jdHeroCard");
    const jdMatchSection  = document.getElementById("jdMatchSection");
    const jdMissingSection = document.getElementById("jdMissingSection");

    if (result.jd_provided) {
      // JD ring
      document.getElementById("jdMatchScore").textContent = analysis.jd_match_score;
      animateRing("jdRingFill", analysis.jd_match_score);
      jdHeroCard.style.display = "flex";

      // Matched keywords — tag chips
      const matchedUl = document.getElementById("matchedKeywords");
      matchedUl.innerHTML = "";
      if (analysis.matched_keywords.length > 0) {
        analysis.matched_keywords.forEach(function (kw) {
          const li = document.createElement("li");
          li.textContent = kw;
          matchedUl.appendChild(li);
        });
      } else {
        const li = document.createElement("li");
        li.textContent = "No matching keywords found.";
        matchedUl.appendChild(li);
      }
      jdMatchSection.style.display = "block";

      // Missing JD keywords — tag chips
      const missingJdUl = document.getElementById("missingJdKeywords");
      missingJdUl.innerHTML = "";
      if (analysis.missing_jd_keywords.length > 0) {
        analysis.missing_jd_keywords.forEach(function (kw) {
          const li = document.createElement("li");
          li.textContent = kw;
          missingJdUl.appendChild(li);
        });
      } else {
        const li = document.createElement("li");
        li.textContent = "No missing keywords — great match!";
        missingJdUl.appendChild(li);
      }
      jdMissingSection.style.display = "block";

    } else {
      jdHeroCard.style.display      = "none";
      jdMatchSection.style.display  = "none";
      jdMissingSection.style.display = "none";
    }

    // ── ATS banner ────────────────────────────────────────────────
    const atsBanner = document.getElementById("atsBanner");
    const atsList   = document.getElementById("atsList");
    atsList.innerHTML = "";

    if (analysis.ats_issues && analysis.ats_issues.length > 0) {
      analysis.ats_issues.forEach(function (issue) {
        const li = document.createElement("li");
        li.textContent = issue;
        atsList.appendChild(li);
      });
      atsBanner.style.display = "flex";
    } else {
      atsBanner.style.display = "none";
    }

    // ── Section score bars ────────────────────────────────────────
    const sectionScoresSection = document.getElementById("sectionScoresSection");
    const sectionScoresList    = document.getElementById("sectionScoresList");
    const sectionScores        = analysis.section_scores;

    if (sectionScores && Object.keys(sectionScores).length > 0) {
      sectionScoresList.innerHTML = "";
      Object.entries(sectionScores).forEach(function ([section, score]) {
        const pct      = Math.min(100, Math.max(0, score));
        const barClass = pct >= 70 ? "bar-good" : pct >= 40 ? "bar-average" : "bar-weak";

        const row = document.createElement("div");
        row.className = "section-score-row";
        row.innerHTML = `
          <div class="section-score-label">
            <span class="section-name">${section}</span>
            <span class="section-pct">${pct}/100</span>
          </div>
          <div class="section-bar-track">
            <div class="section-bar-fill ${barClass}" style="width: 0%"
                 data-target="${pct}%"></div>
          </div>`;
        sectionScoresList.appendChild(row);
      });

      // Animate bars after a short delay
      setTimeout(function () {
        sectionScoresList.querySelectorAll(".section-bar-fill").forEach(function (bar) {
          bar.style.width = bar.dataset.target;
        });
      }, 100);

      sectionScoresSection.style.display = "block";
    } else {
      sectionScoresSection.style.display = "none";
    }

    // ── Section suggestions ───────────────────────────────────────
    const sectionSuggestionsSection = document.getElementById("sectionSuggestionsSection");
    const sectionSuggestionsList    = document.getElementById("sectionSuggestionsList");
    const sectionSuggestions        = analysis.section_suggestions;

    if (sectionSuggestions && Object.keys(sectionSuggestions).length > 0) {
      sectionSuggestionsList.innerHTML = "";
      Object.entries(sectionSuggestions).forEach(function ([section, suggestion]) {
        const li = document.createElement("li");
        li.innerHTML = `<span class="section-suggestion-label">${section}:</span> ${suggestion}`;
        sectionSuggestionsList.appendChild(li);
      });
      sectionSuggestionsSection.style.display = "block";
    } else {
      sectionSuggestionsSection.style.display = "none";
    }

    // ── Show dashboard, hide upload screen ────────────────────────
    uploadScreen.style.display = "none";
    dashboard.style.display    = "flex";
    window.scrollTo({ top: 0, behavior: "smooth" });

  } catch (error) {
    console.error(error);
    showError("Could not connect to the backend. Make sure the server is running.");
  } finally {
    loading.style.display = "none";
  }
});
