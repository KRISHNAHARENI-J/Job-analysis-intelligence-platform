import streamlit as st

from dashboard_ui import fetch_api

st.set_page_config(page_title="Similarity Search", page_icon="🔗", layout="wide")
st.title("Similarity Search")
st.caption("Find listings with similar titles, skills, industries, and descriptions.")

jobs = fetch_api("/api/jobs", params={"limit": 100})["results"]
if not jobs:
    st.info("No jobs are available to compare.")
else:
    jobs_by_id = {job["job_id"]: job for job in jobs}
    job_id = st.selectbox(
        "Choose a job",
        list(jobs_by_id),
        format_func=lambda key: (
            f"{jobs_by_id[key]['title']} — {jobs_by_id[key]['company']} ({key})"
        ),
    )
    selected = jobs_by_id[job_id]
    st.write(f"**{selected['title']}** at {selected['company']}")
    related = fetch_api(
        f"/api/similar/{job_id}",
        params={"limit": 10},
    )["results"]
    if not related:
        st.info("No similar listings were found.")
    else:
        for job in related:
            with st.container(border=True):
                st.subheader(job["title"] or "Untitled role")
                st.write(f"{job['company']} · {job['industry']} · {job['location']}")
                st.progress(min(1.0, max(0.0, job["similarity"])))
                st.caption(f"Text similarity: {job['similarity']:.0%}")
                if job["skills"]:
                    st.write("Skills: " + ", ".join(job["skills"]))
