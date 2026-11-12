import json
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="Job Analysis Dashboard",
    page_icon="📊",
    layout="wide"
)

# JSON report location
JSON_FILE = "data/job_analysis_report_20260914.json"

# Load JSON
with open(JSON_FILE, "r", encoding="utf-8") as file:
    report = json.load(file)

# Title
st.title("📊 Job Analysis Dashboard")
st.write("Job role, industry and skill analysis")

# -------------------------
# TOP RESULTS
# -------------------------

top_result = report["top_result"]

top_role = top_result["job_role"]
top_industry = top_result["industry"]
top_skill = top_result["skill"]

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Top Job Role",
        top_role["role"],
        f'{top_role["count"]} jobs'
    )

with col2:
    st.metric(
        "Top Industry",
        top_industry["industry"],
        f'{top_industry["count"]} jobs'
    )

with col3:
    st.metric(
        "Top Skill",
        top_skill["skill"],
        f'{top_skill["count"]} occurrence'
    )

st.divider()

# -------------------------
# JOB ROLES
# -------------------------

st.header("💼 Most Demanding Job Roles")

roles_df = pd.DataFrame(
    report["most_demanding_job_role"]
)

st.dataframe(
    roles_df,
    use_container_width=True,
    hide_index=True
)

fig, ax = plt.subplots()

ax.barh(
    roles_df["role"],
    roles_df["count"]
)

ax.set_xlabel("Number of Jobs")
ax.set_ylabel("Job Role")
ax.set_title("Job Role Demand")

ax.invert_yaxis()

st.pyplot(fig)

# -------------------------
# INDUSTRIES
# -------------------------

st.header("🏢 Most Demanding Industries")

industry_df = pd.DataFrame(
    report["most_demanding_industry"]
)

st.dataframe(
    industry_df,
    use_container_width=True,
    hide_index=True
)

fig, ax = plt.subplots()

ax.bar(
    industry_df["industry"],
    industry_df["count"]
)

ax.set_xlabel("Industry")
ax.set_ylabel("Number of Jobs")
ax.set_title("Industry Demand")

plt.xticks(rotation=30)

st.pyplot(fig)

# -------------------------
# SKILLS
# -------------------------

st.header("🛠️ Most Demanding Skills")

skills_df = pd.DataFrame(
    report["most_demanding_skills"]
)

st.dataframe(
    skills_df,
    use_container_width=True,
    hide_index=True
)

fig, ax = plt.subplots()

ax.barh(
    skills_df["skill"],
    skills_df["count"]
)

ax.set_xlabel("Number of Jobs")
ax.set_ylabel("Skill")
ax.set_title("Skill Demand")

ax.invert_yaxis()

st.pyplot(fig)

# -------------------------
# RAW JSON
# -------------------------

st.divider()

with st.expander("View Raw JSON Report"):
    st.json(report)