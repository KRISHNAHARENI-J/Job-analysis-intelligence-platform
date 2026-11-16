import json

import streamlit as st

from dashboard_ui import fetch_api

st.set_page_config(page_title="Knowledge Graph", page_icon="🕸️", layout="wide")
st.title("Knowledge Graph")
st.caption("Explore job, industry, and skill relationships stored in Neo4j.")

graph = fetch_api("/api/knowledge-graph")
if not graph["configured"]:
    st.info(graph["message"])
    st.markdown(
        "Expected relationships: `(:Job)-[:IN_INDUSTRY]->(:Industry)` and "
        "`(:Job)-[:REQUIRES]->(:Skill)`. See the README for connection setup."
    )
elif not graph["nodes"]:
    st.info("Neo4j is connected, but no matching job relationships were found.")
else:
    graphviz = [
        "digraph JobMarket {",
        "rankdir=LR;",
        'node [shape=box, style="rounded,filled", fillcolor="#e8f0fe"];',
        'jobs [label="Jobs", fillcolor="#dce8ff"];',
    ]
    for index, node in enumerate(graph["nodes"]):
        node_id = f"node_{index}"
        label = f"{node['label']}\n{node['count']} jobs"
        graphviz.append(f"{node_id} [label={json.dumps(label)}];")
        edge_label = node["type"]
        graphviz.append(
            f"jobs -> {node_id} [label={json.dumps(edge_label)}];"
        )
    graphviz.append("}")
    st.graphviz_chart("\n".join(graphviz), width="stretch")
    st.dataframe(
        [
            {
                "Type": node["type"],
                "Industry or skill": node["label"],
                "Connected jobs": node["count"],
            }
            for node in graph["nodes"]
        ],
        width="stretch",
        hide_index=True,
    )
