import streamlit as st

from dashboard_ui import fetch_api

st.set_page_config(page_title="AI Chat", page_icon="💬", layout="wide")
st.title("AI Chat")
st.caption(
    "Ask questions about the indexed job listings. Answers are retrieval-based "
    "and cite matching records from the dataset."
)

if "job_chat_history" not in st.session_state:
    st.session_state.job_chat_history = []

for message in st.session_state.job_chat_history:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if message.get("sources"):
            with st.expander("Retrieved job records"):
                for source in message["sources"]:
                    st.markdown(
                        f"**{source['title']}** — {source['company']} · "
                        f"{source['industry']} · {source['location']}"
                    )
                    st.caption(source["description"] or "No description available.")

prompt = st.chat_input("Ask about roles, skills, companies, or industries")
if prompt:
    st.session_state.job_chat_history.append({"role": "user", "content": prompt})
    response = fetch_api(
        "/api/chat",
        method="POST",
        payload={"message": prompt, "limit": 3},
    )
    st.session_state.job_chat_history.append(
        {
            "role": "assistant",
            "content": response["answer"],
            "sources": response["sources"],
        }
    )
    st.rerun()

if st.button("Clear conversation"):
    st.session_state.job_chat_history = []
    st.rerun()
