# Job Market Intelligence Dashboard

A multipage Streamlit dashboard backed by a FastAPI service. The API reads job
listings from the configured Excel workbook; it does not require PostgreSQL.

## Dashboard pages

- **Dashboard** — listing, role, industry, and skill KPIs.
- **Job Explorer** — search and filter job listings.
- **Skill Analytics** — most frequently listed skills.
- **Industry Analytics** — compare listing volumes, roles, and skills.
- **Knowledge Graph** — optional Neo4j industry and skill relationships.
- **Similarity Search** — TF-IDF similarity across job listing text.
- **AI Chat** — retrieval-based answers with matching job records as sources.

The chat page uses local TF-IDF retrieval and templates its response from the
retrieved records. It does not call an external generative AI service.

## Run locally

Use Python 3.11. From the repository root in PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dashboard.txt
Copy-Item .env.example .env
```

In the first terminal, start the API:

```powershell
uvicorn api:app --reload --host 127.0.0.1 --port 8001
```

In a second terminal, start the Streamlit dashboard:

```powershell
streamlit run app.py
```

Open the Streamlit URL printed by the command. The API is available at
`http://127.0.0.1:8001`; its interactive API documentation is at `/docs`.

Set `JOB_DATA_FILE` to a workbook path relative to the repository root or to an
absolute path. The default is `annotated_job_training_dataset.xlsx`.

### Neo4j

The Knowledge Graph page is optional. Configure `NEO4J_URI`, `NEO4J_USERNAME`,
`NEO4J_PASSWORD`, and optionally `NEO4J_DATABASE` in the environment (or `.env`).
The graph query expects nodes and relationships in this shape:

```cypher
(:Job)-[:IN_INDUSTRY]->(:Industry {name: "Technology"})
(:Job)-[:REQUIRES]->(:Skill {name: "Python"})
```

## Tests

```powershell
python -m unittest discover -s tests -v
```

## Deploy from GitHub with Render

1. Push this repository to GitHub. Do not commit `.env` or database credentials;
   `.env.example` contains placeholders only.
2. In Render, choose **New → Blueprint**, connect the GitHub repository, and
   apply the included `render.yaml`. This creates separate API and Streamlit
   web services. Render installs the dashboard-only dependency list and starts
   both services from the same commit.
3. Confirm the dashboard service's `API_BASE_URL` points to the API service
   host. The Blueprint wires it automatically; if you rename the API service,
   update that variable to its Render hostname.
4. If using Neo4j, add `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`, and
   optionally `NEO4J_DATABASE` as secret environment variables on the API
   service in Render.
5. Check the API service's `/health` and `/docs` endpoints, then open the
   dashboard service URL.

The GitHub Actions workflow runs the dashboard unit tests on pushes to `main`
and pull requests. After the Blueprint is linked, Render can redeploy from
GitHub when the configured branch changes.
