import streamlit as st
import json
import tempfile
from pathlib import Path
import pandas as pd

from src.extractors.csv_extractor import extract_csv
from src.extractors.resume_extractors import extract_resume_text
from src.merge import group_by_candidate, build_canonical_profile
from src.project_output import load_config, project_profile


# ---------------- PAGE CONFIG ---------------- #

st.set_page_config(
    page_title="TalentSync",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ---------------- CSS ---------------- #

st.markdown("""
<style>

#MainMenu{
visibility:hidden;
}

footer{
visibility:hidden;
}

header{
visibility:hidden;
}

.block-container{
padding-top:2rem;
padding-bottom:2rem;
max-width:1250px;
}

.stApp{
background:#0F172A;
}

/* ---------------- HEADER ---------------- */

.hero{
background:linear-gradient(135deg,#2563EB,#4F46E5);
padding:35px;
border-radius:22px;
margin-bottom:30px;
box-shadow:0px 10px 35px rgba(0,0,0,.25);
}

.hero-title{
font-size:44px;
font-weight:800;
color:white;
margin-bottom:6px;
}

.hero-sub{
font-size:18px;
color:#E5E7EB;
}

/* ---------------- Cards ---------------- */

.card{

background:#1E293B;
border:1px solid #334155;
border-radius:18px;
padding:24px;

}

/* ---------------- Titles ---------------- */

.section-title{

font-size:20px;
font-weight:700;
margin-bottom:15px;
color:white;

}

.small-text{

font-size:14px;
color:#94A3B8;

}

/* ---------------- Upload ---------------- */

[data-testid="stFileUploader"]{

background:#111827;
border:1px solid #334155;
border-radius:14px;
padding:12px;

}

/* ---------------- Select ---------------- */

[data-baseweb="select"]{

border-radius:12px;

}

/* ---------------- Checkbox ---------------- */

.stCheckbox{

margin-top:10px;

}

/* ---------------- Button ---------------- */

.stButton button{

width:100%;
height:56px;

font-size:18px;
font-weight:700;

border-radius:12px;

background:linear-gradient(90deg,#2563EB,#4F46E5);

color:white;

border:none;

transition:0.2s;

}

.stButton button:hover{

transform:translateY(-2px);

}

/* ---------------- Metrics ---------------- */

.metric-card{

background:#111827;

border:1px solid #334155;

border-radius:16px;

padding:22px;

text-align:center;

}

.metric-number{

font-size:34px;

font-weight:800;

color:#60A5FA;

}

.metric-label{

font-size:14px;

color:#94A3B8;

}

/* ---------------- Expanders ---------------- */

div[data-testid="stExpander"]{

border-radius:14px;

border:1px solid #334155;

background:#111827;

}

/* ---------------- Download Button ---------------- */

.stDownloadButton button{

width:100%;

border-radius:12px;

font-weight:600;

}

/* ---------------- JSON ---------------- */

[data-testid="stJson"]{

border-radius:12px;

}

/* ---------------- Divider ---------------- */

hr{

margin-top:30px;
margin-bottom:30px;

}

</style>
""", unsafe_allow_html=True)


# ---------------- HERO ---------------- #

st.markdown("""
<div class="hero">

<div class="hero-title">
💠 TalentSync
</div>

<div class="hero-sub">
One Candidate • One Unified Profile • Multiple Sources
</div>

</div>
""", unsafe_allow_html=True)


# ---------------- TOP DASHBOARD ---------------- #

left, right = st.columns([1.45, 1])

with left:

    st.markdown("## 📂 Upload Sources")
    st.caption("Upload recruiter CSV files and candidate resumes.")

    csv_file = st.file_uploader(
        "Recruiter CSV",
        type=["csv"],
        help="CSV exported from recruiter database."
    )

    resume_files = st.file_uploader(
        "Candidate Resume(s)",
        type=["txt", "pdf", "docx"],
        accept_multiple_files=True,
        help="Upload one or more resumes."
    )


with right:

    st.markdown("## ⚙️ Pipeline Settings")
    st.caption("Choose how the final candidate profile should look.")

    config_choice = st.selectbox(
        "Output Configuration",
        [
            "default_config.json",
            "minimal_config.json"
        ]
    )

    show_raw_diff = st.checkbox(
        "Show raw per-source comparison",
        value=True
    )

    st.write("")
    st.write("")

    run_button = st.button(
        "🚀 Run TalentSync Pipeline",
        use_container_width=True
    )


st.divider()
if run_button:

    if not csv_file and not resume_files:
        st.warning("⚠️ Upload at least one CSV or Resume before running the pipeline.")
        st.stop()

    with st.spinner("Running TalentSync Pipeline..."):

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

    st.success("✅ Pipeline completed successfully!")

    st.markdown("## 📊 Pipeline Summary")

    m1, m2, m3 = st.columns(3)

    with m1:
        st.metric(
            "Candidates",
            len(groups)
        )

    with m2:
        st.metric(
            "Input Sources",
            len(all_records)
        )

    with m3:
        st.metric(
            "Output Config",
            config_choice.replace("_config.json", "").title()
        )

    st.divider()

    st.markdown("## 📥 Export")

    flat_rows = []

    for key, records in groups.items():

        candidate_id_tmp = f"C{list(groups.keys()).index(key)+1:03d}"

        profile_tmp = build_canonical_profile(candidate_id_tmp, records)

        flat_rows.append({

            "candidate_id": profile_tmp.candidate_id,

            "full_name": profile_tmp.full_name.value if profile_tmp.full_name else None,

            "phones": "; ".join(
                p.value["number"] for p in profile_tmp.phones
            ),

            "emails": "; ".join(
                profile_tmp.emails
            ),

            "headline": profile_tmp.headline.value if profile_tmp.headline else None,

            "skills": ", ".join(
                s.name for s in profile_tmp.skills
            ),

            "overall_confidence": profile_tmp.overall_confidence,

        })

    csv_df = pd.DataFrame(flat_rows)

    st.download_button(

        "⬇️ Download Merged Profiles (CSV)",

        data=csv_df.to_csv(index=False),

        file_name="merged_candidates.csv",

        mime="text/csv",

        use_container_width=True,

    )

    st.divider()

    st.markdown("## 👥 Unified Candidate Profiles")

    for idx, (key, records) in enumerate(groups.items(), start=1):

        candidate_id = f"C{idx:03d}"

        profile = build_canonical_profile(candidate_id, records)

        projected = project_profile(profile, config)

        

        with st.expander(

            f"👤 {key}   |   {candidate_id}",

            expanded=(idx == 1)

        ):

            c1, c2 = st.columns(2)

            with c1:
                st.metric(
                    "Sources",
                    len(records)
                )

            with c2:
                st.metric(
                    "Overall Confidence",
                    f"{profile.overall_confidence:.2f}"
                )

            st.markdown("### Canonical Profile")

            st.json(projected)

            if show_raw_diff and len(records) > 1:

                st.markdown("---")

                st.markdown("### 🔍 Raw Source Comparison")

                diff_cols = st.columns(len(records))

                for c, rec in zip(diff_cols, records):

                    with c:

                        st.caption(
                            f"📄 {rec.source_name}"
                        )

                        st.caption(
                            f"Method : {rec.method}"
                        )

                        st.json(
                            rec.model_dump(
                                exclude={"raw_text"}
                            )
                        )

    st.success(
        f"🎉 Successfully generated {len(groups)} unified candidate profile(s)."
    )