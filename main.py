 #This is a sample from __future__ import annotations

import ast
import json
import pickle
import re
from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline


INPUT_FILE = Path("data/jobs_with_nlp1.xlsx")
MODEL_DIR = Path("trained_job_models")
RANDOM_STATE = 42

INDUSTRY_KEYWORDS = {
	"Healthcare": ("health", "medical", "clinic", "pharma", "care", "biotech", "hospital"),
	"Technology": ("tech", "software", "systems", "digital", "ai", "it", "data", "labs"),
	"Finance": ("bank", "finance", "financial", "capital", "insurance", "risk"),
	"Manufacturing": ("engineering", "manufacturing", "industrial", "automotive", "electronics"),
	"Consulting": ("consulting", "services", "advisory"),
	"Retail": ("retail", "commerce", "consumer", "ecommerce"),
}

CATEGORY_KEYWORDS = {
	"Data and Analytics": ("data", "analyst", "analytics", "bi ", "business intelligence"),
	"Software Engineering": ("developer", "software", "engineer", "programmer", "devops"),
	"Cloud and Infrastructure": ("cloud", "network", "infrastructure", "system administrator", "sre"),
	"Management": ("manager", "director", "lead", "supervisor", "product owner"),
	"Design": ("designer", "ux", "ui", "creative"),
	"Sales and Marketing": ("sales", "marketing", "account executive", "business development"),
	"Human Resources": ("human resources", "hr ", "recruiter", "talent acquisition"),
	"Other": (),
}


def find_column(dataframe: pd.DataFrame, *names: str) -> str | None:
	normalized = {re.sub(r"[^a-z0-9]", "", column.lower()): column for column in dataframe.columns}
	for name in names:
		match = normalized.get(re.sub(r"[^a-z0-9]", "", name.lower()))
		if match:
			return match
	return None


def text_value(value: object) -> str:
	if value is None or pd.isna(value):
		return ""
	return str(value).strip()


def parse_skills(value: object) -> list[str]:
	raw = text_value(value)
	if not raw or raw.lower() in {"nan", "none", "[]"}:
		return []
	try:
		parsed = ast.literal_eval(raw)
		if isinstance(parsed, list):
			return [text_value(item) for item in parsed if text_value(item)]
	except (SyntaxError, ValueError):
		pass
	return [part.strip(" []'\"") for part in re.split(r"[,;|]", raw) if part.strip(" []'\"")]


def keyword_label(value: str, keywords: dict[str, tuple[str, ...]]) -> str:
	lowered = value.lower()
	for label, label_keywords in keywords.items():
		if any(keyword in lowered for keyword in label_keywords):
			return label
	return "Other"


def build_labels(dataframe: pd.DataFrame) -> pd.DataFrame:
	title_column = find_column(dataframe, "job_title", "job title", "title")
	company_column = find_column(dataframe, "company_name", "company name", "company")
	skills_column = find_column(dataframe, "required_skills", "required skills", "skills", "skill")

	titles = dataframe[title_column].map(text_value) if title_column else pd.Series("", index=dataframe.index)
	companies = dataframe[company_column].map(text_value) if company_column else pd.Series("", index=dataframe.index)
	skills = dataframe[skills_column].map(parse_skills) if skills_column else pd.Series([[]] * len(dataframe), index=dataframe.index)

	labels = pd.DataFrame(index=dataframe.index)
	label_sources = {
		"job_category": ("job_category", "job category", "category"),
		"industry": ("industry", "job_industry"),
		"skill": ("skill", "primary_skill", "primary skill"),
		"role": ("role", "job_role", "job role", "role_title"),
	}
	for label, candidates in label_sources.items():
		source = find_column(dataframe, *candidates)
		labels[label] = dataframe[source].map(text_value) if source else ""

	labels["job_category"] = labels["job_category"].where(
		labels["job_category"].ne(""), titles.map(lambda value: keyword_label(value, CATEGORY_KEYWORDS))
	)
	labels["industry"] = labels["industry"].where(
		labels["industry"].ne(""), (companies + " " + titles).map(lambda value: keyword_label(value, INDUSTRY_KEYWORDS))
	)
	labels["skill"] = labels["skill"].where(
		labels["skill"].ne(""), skills.map(lambda values: values[0] if values else "Unknown")
	)
	labels["role"] = labels["role"].where(labels["role"].ne(""), titles)
	return labels


def build_features(dataframe: pd.DataFrame) -> pd.Series:
	preferred_columns = [
		("job_title", "job title", "title"),
		("company_name", "company name", "company"),
		("location",),
		("experience_years", "experience years", "experience"),
		("education_level", "education level", "education"),
		("required_skills", "required skills", "skills", "skill"),
	]
	columns = [find_column(dataframe, *names) for names in preferred_columns]
	columns = [column for column in columns if column]
	if not columns:
		raise ValueError("No usable feature columns were found in the workbook.")

	def combine(row: pd.Series) -> str:
		values = []
		for column in columns:
			value = row[column]
			values.extend(parse_skills(value) if "skill" in column.lower() else [text_value(value)])
		return " ".join(value for value in values if value)

	return dataframe.apply(combine, axis=1)


def make_models() -> dict[str, Pipeline]:
	vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)
	return {
		"logistic_regression": Pipeline([
			("tfidf", vectorizer),
			("classifier", LogisticRegression(max_iter=1000, class_weight="balanced")),
		]),
		"random_forest": Pipeline([
			("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)),
			("classifier", RandomForestClassifier(n_estimators=250, random_state=RANDOM_STATE, class_weight="balanced")),
		]),
		"naive_bayes": Pipeline([
			("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)),
			("classifier", MultinomialNB()),
		]),
	}


def train_task(features: pd.Series, target: pd.Series, task_name: str) -> dict[str, dict[str, float]]:
	valid = target.ne("") & features.ne("")
	features = features[valid]
	target = target[valid]
	if target.nunique() < 2:
		print(f"Skipping {task_name}: at least two classes are required.")
		return {}

	stratify = target if target.value_counts().min() >= 2 else None
	x_train, x_test, y_train, y_test = train_test_split(
		features, target, test_size=0.2, random_state=RANDOM_STATE, stratify=stratify
	)
	results = {}
	for model_name, model in make_models().items():
		model.fit(x_train, y_train)
		predictions = model.predict(x_test)
		results[model_name] = {"accuracy": float(accuracy_score(y_test, predictions))}
		print(f"\n{task_name} / {model_name}")
		print(classification_report(y_test, predictions, zero_division=0))
		MODEL_DIR.mkdir(exist_ok=True)
		with (MODEL_DIR / f"{task_name}_{model_name}.pkl").open("wb") as model_file:
			pickle.dump(model, model_file)
	return results


def main() -> None:
	if not INPUT_FILE.exists():
		raise FileNotFoundError(f"Input file not found: {INPUT_FILE.resolve()}")

	dataframe = pd.read_excel(INPUT_FILE)
	dataframe = dataframe.dropna(how="all").reset_index(drop=True)
	labels = build_labels(dataframe)
	features = build_features(dataframe)

	print(f"Loaded {len(dataframe)} rows from {INPUT_FILE}")
	print("Derived/loaded label counts:")
	print(labels.nunique().to_string())

	all_results = {
		task: train_task(features, labels[task], task)
		for task in ("job_category", "industry", "skill", "role")
	}
	MODEL_DIR.mkdir(exist_ok=True)
	(MODEL_DIR / "metrics.json").write_text(json.dumps(all_results, indent=2), encoding="utf-8")
	print(f"\nSaved models and metrics to: {MODEL_DIR.resolve()}")


#if __name__ == "__main__":
#	main()
#	Python script.

#Press Shift+F10 to execute it or replace it with your code.
#Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.




#See PyCharm help at https://www.jetbrains.com/help/pycharm/
