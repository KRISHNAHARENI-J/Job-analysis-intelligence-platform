import os
import re
from collections import Counter
from functools import lru_cache
from math import log, sqrt
from pathlib import Path
from typing import Any

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_FILE = ROOT_DIR / "annotated_job_training_dataset.xlsx"


def _normalized_name(name: object) -> str:
    return re.sub(r"[^a-z0-9]", "", str(name).lower())


def _text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "; ".join(_text(item) for item in value if _text(item))
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    result = str(value).strip()
    return "" if result.lower() in {"nan", "none", "null"} else result


def parse_skills(value: object) -> list[str]:
    if isinstance(value, list):
        parts = [_text(item) for item in value]
    else:
        raw = _text(value)
        if not raw or raw.lower() in {"not specified", "[]"}:
            return []
        parts = re.split(r"[;|,\n]+", raw)

    skills: list[str] = []
    seen: set[str] = set()
    for part in parts:
        skill = _text(part).strip(" .")
        key = skill.casefold()
        if skill and key not in seen:
            skills.append(skill)
            seen.add(key)
    return skills


def _find_column(columns: list[object], *names: str) -> object | None:
    normalized = {_normalized_name(column): column for column in columns}
    for name in names:
        match = normalized.get(_normalized_name(name))
        if match is not None:
            return match
    return None


def _first_nonempty(*values: object) -> str:
    for value in values:
        result = _text(value)
        if result and result.lower() not in {"not specified", "[]"}:
            return result
    return ""


def _format_date(value: object) -> str | None:
    raw = _text(value)
    if not raw:
        return None
    parsed = pd.to_datetime(value, errors="coerce", dayfirst=True)
    if pd.isna(parsed):
        return raw
    return parsed.date().isoformat()


def normalize_jobs(frame: pd.DataFrame) -> pd.DataFrame:
    """Map the project's workbook columns to a consistent dashboard schema."""
    frame = frame.dropna(how="all").reset_index(drop=True)
    columns = list(frame.columns)

    def values(*names: str) -> pd.Series:
        column = _find_column(columns, *names)
        if column is None:
            return pd.Series("", index=frame.index, dtype="object")
        return frame[column]

    skills_columns = [
        _find_column(columns, name)
        for name in (
            "SKILL CATEGORY",
            "EXTRACTED_SKILLS",
            "required_skills",
            "SKILLSETS",
            "skills",
        )
    ]
    skills_columns = [column for column in skills_columns if column is not None]

    jobs = pd.DataFrame(index=frame.index)
    jobs["job_id"] = [f"job-{index}" for index in frame.index]
    jobs["title"] = values("JOB TITLE", "title", "ROLE", "job_role").map(_text)
    jobs["company"] = values("COMPANY NAME", "company", "employer").map(_text)
    jobs["industry"] = values("INDUSTRY", "job_industry").map(_text)
    jobs["location"] = values("LOCATION", "city", "region").map(_text)
    jobs["experience"] = values(
        "EXPERIENCE", "EXPERIENCE_REQUIRED", "experience_years"
    ).map(_text)
    jobs["posted_date"] = values("JOB POSTED DATE", "posted_date", "date_posted").map(
        _format_date
    )
    jobs["description"] = values(
        "JOB DESCRIPTION", "description", "job_description"
    ).map(_text)
    jobs["url"] = values("JOB URL", "url", "job_url").map(_text)
    jobs["category"] = values("JOB CATEGORY", "JOB_CATEGORY", "category").map(_text)

    if skills_columns:
        jobs["skills"] = frame[skills_columns].apply(
            lambda row: parse_skills(
                _first_nonempty(*(row[column] for column in skills_columns))
            ),
            axis=1,
        )
    else:
        jobs["skills"] = [[] for _ in frame.index]

    return jobs.reset_index(drop=True)


@lru_cache(maxsize=2)
def _load_jobs_cached(data_file: str) -> pd.DataFrame:
    path = Path(data_file)
    if not path.is_absolute():
        path = ROOT_DIR / path
    if not path.is_file():
        raise FileNotFoundError(f"Job data workbook not found: {path}")
    return normalize_jobs(pd.read_excel(path))


def load_jobs() -> pd.DataFrame:
    configured_path = os.getenv("JOB_DATA_FILE", str(DEFAULT_DATA_FILE))
    return _load_jobs_cached(configured_path).copy()


def filter_jobs(
    jobs: pd.DataFrame,
    *,
    query: str = "",
    industry: str = "",
    skill: str = "",
    location: str = "",
) -> pd.DataFrame:
    filtered = jobs
    if query.strip():
        searchable = filtered[
            ["title", "company", "industry", "location", "experience", "description"]
        ].fillna("").astype(str).agg(" ".join, axis=1)
        searchable = searchable + " " + filtered["skills"].map(
            lambda items: " ".join(items)
        )
        filtered = filtered[searchable.str.contains(query.strip(), case=False, regex=False)]
    if industry:
        filtered = filtered[
            filtered["industry"].str.casefold() == industry.casefold()
        ]
    if skill:
        filtered = filtered[
            filtered["skills"].map(
                lambda items: any(skill.casefold() in item.casefold() for item in items)
            )
        ]
    if location:
        filtered = filtered[
            filtered["location"].str.casefold() == location.casefold()
        ]
    return filtered.copy()


def _count_values(values: pd.Series, limit: int = 10) -> list[dict[str, Any]]:
    counts = values.dropna().astype(str).str.strip()
    counts = counts[counts.ne("")].value_counts().head(limit)
    return [{"label": str(name), "count": int(count)} for name, count in counts.items()]


def build_analytics(jobs: pd.DataFrame) -> dict[str, Any]:
    skill_values = jobs["skills"].explode()
    return {
        "total_jobs": int(len(jobs)),
        "industry_options": sorted(
            value for value in jobs["industry"].dropna().unique().tolist() if value
        ),
        "location_options": sorted(
            value for value in jobs["location"].dropna().unique().tolist() if value
        ),
        "top_roles": _count_values(jobs["title"]),
        "top_industries": _count_values(jobs["industry"]),
        "top_skills": _count_values(skill_values),
    }


def _job_text(job: pd.Series) -> str:
    return " ".join(
        [
            _text(job.get("title")),
            _text(job.get("company")),
            _text(job.get("industry")),
            _text(job.get("location")),
            _text(job.get("category")),
            " ".join(job.get("skills", [])),
            _text(job.get("description")),
        ]
    )


def _tokens(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", text.casefold())
    stopwords = {
        "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
        "in", "is", "it", "of", "on", "or", "that", "the", "to", "with",
    }
    words = [word for word in words if word not in stopwords]
    return words + [f"{left} {right}" for left, right in zip(words, words[1:])]


def _rank_jobs(jobs: pd.DataFrame, query: str, limit: int) -> list[dict[str, Any]]:
    if jobs.empty:
        return []
    documents = [_job_text(row) for _, row in jobs.iterrows()]
    if not any(document.strip() for document in documents):
        return []

    document_terms = [Counter(_tokens(document)) for document in documents]
    document_frequency: Counter[str] = Counter()
    for terms in document_terms:
        document_frequency.update(terms.keys())
    document_count = len(documents)
    inverse_frequency = {
        term: log((document_count + 1) / (frequency + 1)) + 1
        for term, frequency in document_frequency.items()
    }

    query_counts = Counter(_tokens(query))
    query_vector = {
        term: count * inverse_frequency[term]
        for term, count in query_counts.items()
        if term in inverse_frequency
    }
    query_norm = sqrt(sum(weight * weight for weight in query_vector.values()))
    scores: list[float] = []
    for terms in document_terms:
        vector = {
            term: count * inverse_frequency[term]
            for term, count in terms.items()
        }
        vector_norm = sqrt(sum(weight * weight for weight in vector.values()))
        dot_product = sum(
            weight * vector.get(term, 0.0) for term, weight in query_vector.items()
        )
        scores.append(
            dot_product / (query_norm * vector_norm)
            if query_norm and vector_norm
            else 0.0
        )
    ranked = sorted(
        ((index, float(score)) for index, score in enumerate(scores) if score > 0),
        key=lambda item: (-item[1], item[0]),
    )[:limit]
    results: list[dict[str, Any]] = []
    for index, score in ranked:
        record = jobs.iloc[index].to_dict()
        record["similarity"] = round(score, 4)
        results.append(record)
    return results


def find_similar_jobs(
    jobs: pd.DataFrame,
    job_id: str,
    limit: int = 5,
) -> list[dict[str, Any]]:
    matching = jobs.index[jobs["job_id"] == job_id].tolist()
    if not matching:
        return []
    source_index = matching[0]
    source_text = _job_text(jobs.loc[source_index])
    candidates = jobs.drop(index=source_index)
    if not source_text.strip():
        return []
    return _rank_jobs(candidates, source_text, limit)


def retrieve_jobs(
    jobs: pd.DataFrame,
    query: str,
    limit: int = 3,
) -> list[dict[str, Any]]:
    return _rank_jobs(jobs, query, limit)


def json_records(jobs: pd.DataFrame) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for record in jobs.to_dict(orient="records"):
        records.append(
            {
                key: (value if value is not None and not pd.isna(value) else None)
                if key != "skills"
                else value
                for key, value in record.items()
            }
        )
    return records
