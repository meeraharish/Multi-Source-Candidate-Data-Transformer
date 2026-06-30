import streamlit as st
import json
import tempfile
from pathlib import Path
import pandas as pd 
from src.extractors.csv_extractor import extract_csv
from src.extractors.resume_extractors import extract_resume_text
from src.merge import group_by_candidate, build_canonical_profile
from src.project_output import load_config, project_profile

st.set_page_config(page_title="TalentSync", page_icon="🧩", layout="wide")

st.markdown(
    """
    <style>
    .main-title { font-size: 2.2rem; font-weight: 700; margin-bottom: 0; }
    .main-subtitle { color: #6b7280; font-size: 1rem; margin-top: 0.2rem; margin-bottom: 1.5rem; }
    .stExpander { border: 1px solid #e5e7eb; border-radius: 10px; margin-bottom: 0.75rem; }
    .metric-pill {
        display: inline-block; padding: 2px 10px; border-radius: 999px;
        background-color: #eef2ff; color: #4338ca; font-size: 0.8rem; font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<p class="main-title">🧩 TalentSync</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="main-subtitle">One Candidate. One Profile. Multiple Sources.</p>',
    unsafe_allow_html=True,
)

with st.container():
    col1, col2 = st.columns([1.2, 1])

    with col1:
        st.markdown("**1. Upload your sources**")
        csv_file = st.file_uploader("Recruiter CSV", type=["csv"])
        resume_files = st.file_uploader(
            "Resume(s) — .txt, .pdf, or .docx",
            type=["txt", "pdf", "docx"],
            accept_multiple_files=True,
        )

    with col2:
        st.markdown("**2. Choose output shape**")
        config_choice = st.selectbox("Output config", ["default_config.json", "minimal_config.json"])
        show_raw_diff = st.checkbox("Show raw per-source diff view", value=True)
        st.markdown("**3. Run**")
        run_button = st.button("Run pipeline", type="primary", use_container_width=True)

st.divider()

if run_button:
    if not csv_file and not resume_files:
        st.warning("Upload at least one file (CSV and/or resumes) before running.")
        st.stop()

    all_records = []

    if csv_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
            tmp.write(csv_file.getvalue())
            tmp_path = tmp.name
        csv_records = extract_csv(tmp_path)
        all_records.extend(csv_records)

    for rf in resume_files:
        suffix = Path(rf.name).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(rf.getvalue())
            tmp_path = tmp.name
        recs = extract_resume_text(tmp_path)
        all_records.extend(recs)

    groups = group_by_candidate(all_records)
    config = load_config(f"config/{config_choice}")

    st.subheader(f"📋 Merged Profiles — {len(groups)} candidate(s) found")
    

    flat_rows = []
    for key, records in groups.items():
        candidate_id_tmp = f"C{list(groups.keys()).index(key) + 1:03d}"
        profile_tmp = build_canonical_profile(candidate_id_tmp, records)
        flat_rows.append({
            "candidate_id": profile_tmp.candidate_id,
            "full_name": profile_tmp.full_name.value if profile_tmp.full_name else None,
            "phones": "; ".join(p.value["number"] for p in profile_tmp.phones),
            "emails": "; ".join(profile_tmp.emails),
            "headline": profile_tmp.headline.value if profile_tmp.headline else None,
            "skills": ", ".join(s.name for s in profile_tmp.skills),
            "overall_confidence": profile_tmp.overall_confidence,
        })

    csv_df = pd.DataFrame(flat_rows)
    st.download_button(
        "⬇️ Download merged profiles as CSV",
        data=csv_df.to_csv(index=False),
        file_name="merged_candidates.csv",
        mime="text/csv",
    )
    for idx, (key, records) in enumerate(groups.items(), start=1):
        candidate_id = f"C{idx:03d}"
        profile = build_canonical_profile(candidate_id, records)
        projected = project_profile(profile, config)

        source_count = len(records)
        pill = f'<span class="metric-pill">{source_count} source(s) · confidence {profile.overall_confidence}</span>'

        with st.expander(f"{candidate_id} — {key}", expanded=(idx == 1)):
            st.markdown(pill, unsafe_allow_html=True)
            st.json(projected)

            if show_raw_diff and len(records) > 1:
                st.markdown("**Raw per-source extraction (before merge):**")
                diff_cols = st.columns(len(records))
                for c, rec in zip(diff_cols, records):
                    with c:
                        st.caption(f"Source: {rec.source_name} ({rec.method})")
                        st.json(rec.model_dump(exclude={"raw_text"}))