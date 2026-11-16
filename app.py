import streamlit as st

from dashboard_ui import fetch_api

st.set_page_config(
    page_title="Job Market Intelligence",
    page_icon="📊",
    layout="wide",
)

st.title("Job Market Intelligence")
st.caption("Explore demand across job roles, skills, and industries.")

analytics = fetch_api("/api/analytics")
jobs_count = analytics["total_jobs"]
roles = analytics["top_roles"]
industries = analytics["top_industries"]
skills = analytics["top_skills"]

first_role = roles[0]["label"] if roles else "—"
first_industry = industries[0]["label"] if industries else "—"
first_skill = skills[0]["label"] if skills else "—"

col1, col2, col3, col4 = st.columns(4)
col1.metric("Job listings", jobs_count)
col2.metric("Industries", len(analytics["industry_options"]))
col3.metric("Top role", first_role)
col4.metric("Top skill", first_skill)

st.divider()
left, right = st.columns(2)
with left:
    st.subheader("Most common job roles")
    if roles:
        st.bar_chart(
            {item["label"]: item["count"] for item in roles},
            horizontal=True,
        )
    else:
        st.info("No job-role data is available.")

with right:
    st.subheader("Hiring by industry")
    if industries:
        st.bar_chart(
            {item["label"]: item["count"] for item in industries},
            horizontal=True,
        )
    else:
        st.info("No industry data is available.")

st.subheader("Trending skills")
if skills:
    st.bar_chart(
        {item["label"]: item["count"] for item in skills},
        horizontal=True,
    )
else:
    st.info("No skill data is available.")

if first_industry != "—":
    st.caption(f"Most represented industry: **{first_industry}**")
