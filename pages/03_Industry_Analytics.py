import streamlit as st

from dashboard_ui import fetch_api

st.set_page_config(page_title="Industry Analytics", page_icon="🏭", layout="wide")
st.title("Industry Analytics")
st.caption("Compare listing volume, popular roles, and in-demand skills by industry.")

analytics = fetch_api("/api/analytics")
options = analytics["industry_options"]
if not options:
    st.info("No industry data is available.")
    st.stop()

selected = st.multiselect(
    "Choose industries to compare",
    options,
    default=options[: min(3, len(options))],
)
if selected:
    comparison = fetch_api(
        "/api/industries/compare",
        params={"industries": selected},
    )["results"]
    st.bar_chart(
        {item["industry"]: item["job_count"] for item in comparison},
        horizontal=True,
    )
    for industry in comparison:
        with st.expander(f"{industry['industry']} — {industry['job_count']} jobs"):
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Common roles**")
                st.dataframe(
                    [
                        {"Role": item["label"], "Listings": item["count"]}
                        for item in industry["top_roles"]
                    ],
                    hide_index=True,
                    width="stretch",
                )
            with col2:
                st.write("**Common skills**")
                st.dataframe(
                    [
                        {"Skill": item["label"], "Listings": item["count"]}
                        for item in industry["top_skills"]
                    ],
                    hide_index=True,
                    width="stretch",
                )
else:
    st.info("Select at least one industry to compare.")
