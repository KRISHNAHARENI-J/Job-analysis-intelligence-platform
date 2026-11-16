import streamlit as st

from dashboard_ui import fetch_api

st.set_page_config(page_title="Skill Analytics", page_icon="🛠️", layout="wide")
st.title("Skill Analytics")
st.caption("Skills are counted from the skill fields in the loaded workbook.")

analytics = fetch_api("/api/analytics")
skills = analytics["top_skills"]
if not skills:
    st.info("No skills were found in the loaded job data.")
else:
    limit = st.slider("Skills to display", min_value=5, max_value=10, value=10)
    displayed = skills[:limit]
    st.bar_chart(
        {item["label"]: item["count"] for item in displayed},
        horizontal=True,
    )
    st.dataframe(
        [{"Skill": item["label"], "Job listings": item["count"]} for item in displayed],
        width="stretch",
        hide_index=True,
    )
