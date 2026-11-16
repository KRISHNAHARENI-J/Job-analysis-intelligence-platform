import os
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError
from pydantic import BaseModel, Field

from job_data import (
    build_analytics,
    filter_jobs,
    find_similar_jobs,
    json_records,
    load_jobs,
    retrieve_jobs,
)

load_dotenv()

app = FastAPI(
    title="Job Market Intelligence API",
    description="Search and analyze the project's job listing dataset.",
    version="1.0.0",
)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    limit: int = Field(default=3, ge=1, le=5)


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "jobs_loaded": len(load_jobs())}


@app.get("/api/analytics")
def analytics() -> dict[str, Any]:
    return build_analytics(load_jobs())


@app.get("/api/jobs")
def jobs(
    query: str = "",
    industry: str = "",
    skill: str = "",
    location: str = "",
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    filtered = filter_jobs(
        load_jobs(),
        query=query,
        industry=industry,
        skill=skill,
        location=location,
    )
    return {
        "total": len(filtered),
        "results": json_records(filtered.iloc[offset : offset + limit]),
    }


@app.get("/api/industries/compare")
def compare_industries(
    industries: list[str] | None = Query(default=None),
) -> dict[str, Any]:
    data = load_jobs()
    selected = industries or build_analytics(data)["industry_options"][:5]
    comparisons: list[dict[str, Any]] = []
    for industry in selected:
        matching = filter_jobs(data, industry=industry)
        industry_analytics = build_analytics(matching)
        comparisons.append(
            {
                "industry": industry,
                "job_count": len(matching),
                "top_roles": industry_analytics["top_roles"][:5],
                "top_skills": industry_analytics["top_skills"][:5],
            }
        )
    return {"results": comparisons}


@app.get("/api/similar/{job_id}")
def similar_jobs(
    job_id: str,
    limit: int = Query(default=5, ge=1, le=20),
) -> dict[str, Any]:
    data = load_jobs()
    if not data["job_id"].eq(job_id).any():
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    return {"results": find_similar_jobs(data, job_id, limit)}


@app.post("/api/chat")
def chat(request: ChatRequest) -> dict[str, Any]:
    data = load_jobs()
    matches = retrieve_jobs(data, request.message, request.limit)
    if not matches:
        return {
            "answer": (
                "I couldn't find a matching listing in the loaded job dataset. "
                "Try a role, skill, company, or industry name."
            ),
            "sources": [],
        }

    titles = ", ".join(
        f"{item['title']} at {item['company']}".strip(" at")
        for item in matches
    )
    return {
        "answer": (
            f"I found {len(matches)} relevant listing(s) in the dataset: {titles}. "
            "The records below contain the supporting details."
        ),
        "sources": matches,
    }


@app.get("/api/knowledge-graph")
def knowledge_graph() -> dict[str, Any]:
    uri = os.getenv("NEO4J_URI", "").strip()
    username = os.getenv("NEO4J_USERNAME", "").strip()
    password = os.getenv("NEO4J_PASSWORD", "")
    if not all((uri, username, password)):
        return {
            "configured": False,
            "nodes": [],
            "edges": [],
            "message": "Configure NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD.",
        }

    database = os.getenv("NEO4J_DATABASE", "neo4j")
    industry_query = """
        MATCH (job:Job)-[:IN_INDUSTRY]->(industry:Industry)
        RETURN industry.name AS label, count(job) AS count
        ORDER BY count DESC
        LIMIT 10
    """
    skill_query = """
        MATCH (job:Job)-[:REQUIRES]->(skill:Skill)
        RETURN skill.name AS label, count(job) AS count
        ORDER BY count DESC
        LIMIT 10
    """
    try:
        with GraphDatabase.driver(uri, auth=(username, password)) as driver:
            driver.verify_connectivity()
            with driver.session(database=database) as session:
                industry_rows = session.run(industry_query).data()
                skill_rows = session.run(skill_query).data()
    except Neo4jError as exc:
        raise HTTPException(
            status_code=503,
            detail="Could not query Neo4j. Verify the configured connection and graph schema.",
        ) from exc

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    for node_type, relationship, rows in (
        ("Industry", "IN_INDUSTRY", industry_rows),
        ("Skill", "REQUIRES", skill_rows),
    ):
        for row in rows:
            label = row.get("label")
            count = row.get("count")
            if label is None or count is None:
                continue
            nodes.append({"type": node_type, "label": str(label), "count": int(count)})
            edges.append(
                {
                    "source": "Jobs",
                    "target": str(label),
                    "type": relationship,
                    "count": int(count),
                }
            )
    return {"configured": True, "nodes": nodes, "edges": edges, "message": ""}
