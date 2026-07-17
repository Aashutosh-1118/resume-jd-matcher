# Resume ↔ JD Matcher

An AI-powered resume screening tool with two modes: a **Student** mode where a candidate checks their own resume against a job description, and an **HR** mode where a recruiter uploads multiple resumes and gets a ranked, exportable shortlist.

Both modes run on the same underlying scoring engine — the only difference is how many resumes get processed and how the results are presented.

## What it does

- **Student mode** — upload one resume and a job description, get a match score, a list of matching and missing skills, and a short verdict.
- **HR mode** — upload up to 10 resumes against one job description, get a ranked table of candidates with scores, and download the results as a CSV.
- **Flexible JD input** — provide the job description either as a file (PDF/DOCX/TXT) or by pasting the text directly.

## How it works

The pipeline runs in three stages, using the Groq API with structured JSON output:

1. **JD parsing** — the job description is parsed once into a structured schema (role, required skills, preferred skills, minimum experience, education requirements, responsibilities) using Pydantic.
2. **Resume parsing** — each resume is parsed into a structured schema (name, contact info, skills, experience, education, projects, certifications), recognizing different section headings (Experience, Work History, Internships, etc.) rather than relying on exact wording.
3. **Scoring** — the parsed JD and resume are compared by the LLM, which returns a match percentage along with matching skills, missing skills, and a short verdict.

In HR mode, resumes are processed concurrently (3 at a time) rather than sequentially, with automatic retry-and-backoff if the API returns a rate-limit response.

## Tech stack

- **Streamlit** — UI
- **Groq API** (`openai/gpt-oss-120b`) — LLM inference
- **Pydantic** — structured output validation
- **pypdf** / **python-docx** — file parsing
- **pandas** — results table and CSV export
- **uv** — dependency and environment management

## Project structure

```
resume-jd-matcher/
├── app.py              # Streamlit UI (mode selection, both flows)
├── resume_engine.py     # Core logic: JD/resume parsing, scoring
├── requirements.txt      # Dependencies for Streamlit Cloud deployment
├── pyproject.toml        # Dependencies for local development (uv)
├── .env                  # Local API key (not committed)
└── .gitignore
```

## Running it locally

```bash
git clone https://github.com/<your-username>/resume-jd-matcher.git
cd resume-jd-matcher
uv add streamlit groq python-dotenv pydantic pypdf python-docx pandas
```

Create a `.env` file in the project root:
```
GROQ_API_KEY=your_groq_api_key_here
```

Run the app:
```bash
uv run streamlit run app.py
```

## Live demo

[Add your Streamlit Cloud link here once deployed]

## Limitations

- **HR mode is capped at 10 resumes per batch.** This is a deliberate rate-limit safeguard for Groq's free tier (requests-per-day, requests-per-minute, and tokens-per-minute limits), not an architectural ceiling. The pipeline itself doesn't limit batch size — the cap exists to keep the app reliable on a free API key.
- **The match score is an LLM's judgment, not a traditional ATS keyword-matching algorithm.** It doesn't replicate how systems like Workday or Greenhouse score resumes; it's a language-model-based comparison of parsed JD and resume content.
- **Parsing quality depends on resume formatting.** Resumes with unconventional layouts, heavy use of tables/columns, or scanned images (rather than selectable text) may parse less reliably.
- **This has been tested on a limited number of resumes so far** — it is not yet validated at scale.

## Possible next steps

- Add caching so re-running a batch with the same JD doesn't reparse it
- Support scanned/image-based resumes via OCR
- Add authentication for HR mode if deployed publicly
- Move to a paid API tier to remove the 10-resume cap
