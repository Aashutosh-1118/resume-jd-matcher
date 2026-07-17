from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import streamlit as st

from resume_engine import analyze_resume, extract_job_description, read_any_document

st.set_page_config(page_title="Resume <-> JD Matcher", page_icon="📄", layout="wide")

# ---------------------------------------------------------------------
# Global styling - bigger, readable type + a professional dark palette
# instead of Streamlit's default look
# ---------------------------------------------------------------------

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, sans-serif !important;
}

.stApp {
    background: #0B0F19;
}

p, label, .stMarkdown, .stRadio label, .stTextArea textarea, .stFileUploader label, .stFileUploader small {
    font-size: 1.05rem !important;
    line-height: 1.6 !important;
    color: #E5E7EB !important;
}

h1 { font-size: 2.6rem !important; font-weight: 800 !important; color: #F8FAFC !important; letter-spacing: -0.02em; }
h2 { font-size: 1.7rem !important; font-weight: 700 !important; color: #F1F5F9 !important; }
h3 { font-size: 1.3rem !important; font-weight: 600 !important; color: #E2E8F0 !important; }

section[data-testid="stSidebar"] {
    background: #10141F;
    border-right: 1px solid #1F2937;
}
section[data-testid="stSidebar"] * { font-size: 1rem !important; }

.stButton > button {
    background: #4F8CFF;
    color: #ffffff;
    border: none;
    border-radius: 10px;
    padding: 0.7rem 1.4rem;
    font-weight: 600;
    font-size: 1.05rem;
    transition: all 0.15s ease;
}
.stButton > button:hover {
    background: #3B72E0;
    transform: translateY(-1px);
    box-shadow: 0 6px 18px rgba(79,140,255,0.35);
}

.mode-card {
    background: #131826;
    border: 1px solid #232A3B;
    border-radius: 16px;
    padding: 2.2rem 1.8rem;
    text-align: center;
    height: 100%;
}
.mode-card h3 { margin-top: 0.6rem !important; }
.mode-card p { color: #94A3B8 !important; font-size: 0.98rem !important; }
.mode-icon { font-size: 2.6rem; }

.landing-title { text-align: center; margin-top: 1.5rem; }
.landing-subtitle { text-align: center; color: #94A3B8 !important; font-size: 1.15rem !important; margin-bottom: 2.5rem; }

.stProgress > div > div > div > div { background-color: #4F8CFF !important; }

[data-testid="stDataFrame"] { font-size: 1rem !important; }

hr { border-color: #232A3B !important; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Session state - remembers which mode the person picked
# ---------------------------------------------------------------------

if "mode" not in st.session_state:
    st.session_state.mode = None


def show_landing():
    st.markdown("<h1 class='landing-title'>Resume &harr; JD Matcher</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p class='landing-subtitle'>AI-powered resume screening for candidates and recruiters</p>",
        unsafe_allow_html=True,
    )

    _, col1, col2, _ = st.columns([1, 2, 2, 1])
    with col1:
        st.markdown(
            """
            <div class='mode-card'>
                <div class='mode-icon'>🎓</div>
                <h3>I'm a Student</h3>
                <p>Check how well your resume matches a job description, and see what's missing.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Continue as Student", use_container_width=True, key="student_btn"):
            st.session_state.mode = "student"
            st.rerun()
    with col2:
        st.markdown(
            """
            <div class='mode-card'>
                <div class='mode-icon'>🏢</div>
                <h3>I'm HR</h3>
                <p>Upload up to 10 resumes against a job description and get a ranked shortlist.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Continue as HR", use_container_width=True, key="hr_btn"):
            st.session_state.mode = "hr"
            st.rerun()


# -----------------------------------------------------------------
# Landing screen - shown first, before anything else
# -----------------------------------------------------------------

if st.session_state.mode is None:
    show_landing()
    st.stop()

# -----------------------------------------------------------------
# Top bar - shows current mode + lets the person switch back
# -----------------------------------------------------------------

top_l, top_r = st.columns([5, 1])
with top_l:
    mode_label = "Student" if st.session_state.mode == "student" else "HR"
    st.markdown(f"### Resume ↔ JD Matcher — {mode_label} mode")
with top_r:
    if st.button("← Change mode"):
        st.session_state.mode = None
        st.rerun()

# -----------------------------------------------------------------
# JD input (shared sidebar, same for both modes)
# -----------------------------------------------------------------

st.sidebar.markdown("## Job Description")
jd_input_mode = st.sidebar.radio("How do you want to give the JD?", ["Upload a file", "Paste text"])

jd_text = None
if jd_input_mode == "Upload a file":
    jd_file = st.sidebar.file_uploader("Upload JD (pdf/docx/txt)", type=["pdf", "docx", "txt"])
    if jd_file:
        jd_text = read_any_document(jd_file)
        if not jd_text:
            st.sidebar.error("Could not read that file.")
else:
    jd_text = st.sidebar.text_area("Paste the JD text here", height=250)

# -----------------------------------------------------------------
# Student mode - single resume
# -----------------------------------------------------------------

if st.session_state.mode == "student":
    st.subheader("Check your resume against a JD")
    resume_file = st.file_uploader("Upload your resume (pdf/docx)", type=["pdf", "docx"])
    run = st.button("Analyze", type="primary", disabled=not (jd_text and resume_file))

    if run:
        with st.spinner("Reading the JD..."):
            job = extract_job_description(jd_text)
        with st.spinner("Analyzing your resume..."):
            try:
                result = analyze_resume(job, resume_file)
            except Exception as e:
                st.error(f"Could not process this resume: {e}")
                st.stop()

        st.subheader(f"Match Score: {result['score']}%")
        st.progress(min(max(int(result["score"]), 0), 100) / 100)

        details = result["details"]
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Matching skills**")
            for s in details.get("matching_skills", []) or ["None found"]:
                st.write("-", s)
        with col2:
            st.markdown("**Missing skills**")
            for s in details.get("missing_skills", []) or ["None"]:
                st.write("-", s)

        st.markdown(f"**Experience requirement met:** {details.get('experience_requirement_met', 'N/A')}")
        st.markdown("**Verdict**")
        st.info(details.get("verdict", "N/A"))

# -----------------------------------------------------------------
# HR mode - bulk, up to 10 resumes
# -----------------------------------------------------------------

else:
    st.subheader("Shortlist candidates")
    resume_files = st.file_uploader(
        "Upload resumes (up to 10, pdf/docx)", type=["pdf", "docx"], accept_multiple_files=True
    )

    if resume_files and len(resume_files) > 10:
        st.warning("Only the first 10 resumes will be processed (free-tier rate limits).")
        resume_files = resume_files[:10]

    top_n = st.sidebar.slider("How many to shortlist?", 1, 10, 5)
    run = st.button("Run batch analysis", type="primary", disabled=not (jd_text and resume_files))

    if run:
        with st.spinner("Reading the JD..."):
            job = extract_job_description(jd_text)

        progress_bar = st.progress(0)
        status = st.empty()
        results, errors = [], []
        total = len(resume_files)

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(analyze_resume, job, f): f for f in resume_files}
            done = 0
            for future in as_completed(futures):
                f = futures[future]
                done += 1
                progress_bar.progress(done / total)
                status.text(f"Processed {done}/{total} - last: {f.name}")
                try:
                    results.append(future.result())
                except Exception as e:
                    errors.append((f.name, str(e)))

        if errors:
            with st.expander(f"{len(errors)} resume(s) failed to process"):
                for name, err in errors:
                    st.write(f"- {name}: {err}")

        if not results:
            st.error("No resumes were processed successfully.")
        else:
            results.sort(key=lambda r: r["score"], reverse=True)
            df = pd.DataFrame(
                [
                    {
                        "Name": r["name"],
                        "Email": r["email"],
                        "Score (%)": r["score"],
                        "Matching Skills": ", ".join(r["details"].get("matching_skills", [])),
                        "Missing Skills": ", ".join(r["details"].get("missing_skills", [])),
                        "Verdict": r["details"].get("verdict", ""),
                    }
                    for r in results
                ]
            )

            st.subheader(f"Top {top_n} shortlisted candidates")
            st.dataframe(df.head(top_n), use_container_width=True)

            st.subheader("All candidates (ranked)")
            st.dataframe(df, use_container_width=True)

            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download full results as CSV", csv, "shortlist_results.csv", "text/csv")