import streamlit as st
import json
import tempfile
from pathlib import Path

from src.extractors.csv_extractor import extract_csv
from src.extractors.resume_extractors import extract_resume_text
from src.merge import group_by_candidate, build_canonical_profile
from src.project_output import load_config, project_profile

st.set_page_config(page_title="Eightfold Candidate Transformer", layout="wide")
st.title("Multi-Source Candidate Data Transformer")
st.caption("Upload a recruiter CSV and/or resumes, choose a config, and see the merged canonical profile.")

col1, col2 = st.columns(2)

with col1:
    csv_file = st.file_uploader("Recruiter CSV", type=["csv"])
    resume_files = st.file_uploader("Resume(s) (.txt)", type=["txt"], accept_multiple_files=True)

with col2:
    config_choice = st.selectbox("Output config", ["default_config.json", "minimal_config.json"])
    show_raw_diff = st.checkbox("Show raw per-source diff view", value=True)

run_button = st.button("Run pipeline", type="primary")

if run_button:
    if not csv_file and not resume_files:
        st.warning("Upload at least one file (CSV and/or resumes).")
        st.stop()

    all_records = []

    if csv_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
            tmp.write(csv_file.getvalue())
            tmp_path = tmp.name
        csv_records = extract_csv(tmp_path)
        all_records.extend(csv_records)

    resume_records_by_file = {}
    for rf in resume_files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
            tmp.write(rf.getvalue())
            tmp_path = tmp.name
        recs = extract_resume_text(tmp_path)
        resume_records_by_file[rf.name] = recs
        all_records.extend(recs)

    groups = group_by_candidate(all_records)
    config = load_config(f"config/{config_choice}")

    st.subheader(f"Merged Profiles ({len(groups)} candidate(s) found)")

    for idx, (key, records) in enumerate(groups.items(), start=1):
        candidate_id = f"C{idx:03d}"
        profile = build_canonical_profile(candidate_id, records)
        projected = project_profile(profile, config)

        with st.expander(f"{candidate_id} — {key} ({len(records)} source record(s))", expanded=(idx == 1)):
            st.json(projected)

            if show_raw_diff and len(records) > 1:
                st.markdown("**Raw per-source extraction (before merge):**")
                diff_cols = st.columns(len(records))
                for c, rec in zip(diff_cols, records):
                    with c:
                        st.caption(f"Source: {rec.source_name} ({rec.method})")
                        st.json(rec.model_dump(exclude={"raw_text"}))