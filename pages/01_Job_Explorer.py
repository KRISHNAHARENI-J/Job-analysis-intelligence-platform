import streamlit as st

from dashboard_ui import fetch_api

st.set_page_config(page_title="Job Explorer", page_icon="🔎", layout="wide")
st.title("Job Explorer")
st.caption("Search and filter the job listings loaded by the API.")

analytics = fetch_api("/api/analytics")
with st.form("job-search"):
    query = st.text_input("Search", placeholder="Role, company, skill, or description")
    col1, col2, col3 = st.columns(3)
    industry = col1.selectbox("Industry", ["All"] + analytics["industry_options"])
    location = col2.selectbox("Location", ["All"] + analytics["location_options"])
    skill = col3.text_input("Skill contains", placeholder="Python, SQL, ...")
    submitted = st.form_submit_button("Search jobs")

params = {"limit": 100}
if submitted:
    if query.strip():
        params["query"] = query.strip()
    if industry != "All":
        params["industry"] = industry
    if location != "All":
        params["location"] = location
    if skill.strip():
        params["skill"] = skill.strip()

result = fetch_api("/api/jobs", params=params)
st.write(f"Found **{result['total']}** matching job(s).")
if result["results"]:
    st.dataframe(
        [
            {
                "Job title": job["title"],
                "Company": job["company"],
                "Industry": job["industry"],
                "Location": job["location"],
                "Experience": job["experience"],
                "Skills": ", ".join(job["skills"]),
            }
            for job in result["results"]
        ],
        width="stretch",
        hide_index=True,
    )
    for job in result["results"]:
        with st.expander(f"{job['title'] or 'Untitled role'} — {job['company'] or 'Company not listed'}"):
            st.write(job["description"] or "No job description available.")
            if job["skills"]:
                st.write("**Skills:** " + ", ".join(job["skills"]))
            if job["url"].startswith(("https://", "http://")):
                st.link_button("Open job listing", job["url"])
else:
    st.info("No jobs matched those filters.")

if result["total"] > len(result["results"]):
    st.caption("Showing the first 100 matches. Narrow your search to see fewer results.")
