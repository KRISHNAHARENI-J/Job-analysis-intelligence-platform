from pathlib import Path
import re
import warnings

import joblib
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report


# ============================================================
# 1. CONFIGURATION
# ============================================================

INPUT_FILE = Path("data/jobs_with_nlp1.xlsx")
MODEL_DIR = Path("trained_models")

RANDOM_STATE = 42


# ============================================================
# 2. LOAD DATASET
# ============================================================

print("=" * 70)
print("LOADING DATASET")
print("=" * 70)

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Dataset not found: {INPUT_FILE}\n"
        f"Make sure jobs_with_nlp1.xlsx is inside the data folder."
    )

df = pd.read_excel(INPUT_FILE)

print(f"Dataset loaded successfully.")
print(f"Rows    : {len(df)}")
print(f"Columns : {len(df.columns)}")

print("\nColumns:")
for column in df.columns:
    print(f"  - {column}")


# ============================================================
# 3. CLEAN COLUMN NAMES
# ============================================================

df.columns = [
    str(column).strip().upper()
    for column in df.columns
]


# ============================================================
# 4. HELPER FUNCTIONS
# ============================================================

def clean_text(value):
    """Convert missing values to empty strings and normalize text."""
    if pd.isna(value):
        return ""

    value = str(value).lower()
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def combine_columns(dataframe, columns):
    """Combine multiple text columns into one text field."""

    existing_columns = [
        column for column in columns
        if column in dataframe.columns
    ]

    if not existing_columns:
        return pd.Series([""] * len(dataframe))

    return dataframe[existing_columns].fillna("").astype(str).agg(
        " ".join,
        axis=1
    ).map(clean_text)


# ============================================================
# 5. CREATE TEXT FEATURES
# ============================================================

# General text used for classification
df["TEXT"] = combine_columns(
    df,
    [
        "JOB TITLE",
        "SKILLSETS",
        "JOB DESCRIPTION",
        "COMPANY NAME",
        "LOCATION",
    ]
)


# Text without JOB TITLE
# Useful when predicting ROLE from skills/description
df["ROLE_TEXT"] = combine_columns(
    df,
    [
        "SKILLSETS",
        "JOB DESCRIPTION",
        "COMPANY NAME",
        "LOCATION",
    ]
)


# Text without SKILLSETS
# Useful when predicting skill category
df["SKILL_TEXT"] = combine_columns(
    df,
    [
        "JOB TITLE",
        "JOB DESCRIPTION",
        "COMPANY NAME",
        "LOCATION",
    ]
)


# ============================================================
# 6. CREATE JOB CATEGORY LABELS
# ============================================================

CATEGORY_KEYWORDS = {

    "Data and Analytics": [
        "data analyst",
        "data scientist",
        "data analytics",
        "data engineer",
        "business intelligence",
        "bi analyst",
        "analytics",
        "sql",
        "power bi",
        "tableau",
    ],

    "Software Engineering": [
        "software engineer",
        "software developer",
        "developer",
        "programmer",
        "backend",
        "frontend",
        "full stack",
        "java",
        "python developer",
        "web developer",
    ],

    "AI and Machine Learning": [
        "machine learning",
        "ml engineer",
        "artificial intelligence",
        "ai engineer",
        "deep learning",
        "nlp",
        "computer vision",
    ],

    "Cloud and Infrastructure": [
        "cloud",
        "devops",
        "aws",
        "azure",
        "gcp",
        "kubernetes",
        "docker",
        "network",
        "infrastructure",
        "system administrator",
    ],

    "Management": [
        "manager",
        "management",
        "director",
        "supervisor",
        "lead",
        "product owner",
        "project manager",
    ],

    "Design": [
        "designer",
        "ui designer",
        "ux designer",
        "graphic designer",
        "creative",
    ],

    "Sales and Marketing": [
        "sales",
        "marketing",
        "business development",
        "account executive",
        "marketing manager",
    ],

    "Human Resources": [
        "human resources",
        "hr",
        "recruiter",
        "recruitment",
        "talent acquisition",
    ],
}


def classify_category(text):
    """Assign an initial job category using keywords."""

    text = clean_text(text)

    scores = {}

    for category, keywords in CATEGORY_KEYWORDS.items():

        score = 0

        for keyword in keywords:

            if keyword in text:
                score += 1

        scores[category] = score

    best_category = max(
        scores,
        key=scores.get
    )

    if scores[best_category] == 0:
        return "Other"

    return best_category


df["JOB_CATEGORY"] = df["TEXT"].apply(
    classify_category
)


# ============================================================
# 7. CREATE ROLE LABELS
# ============================================================

def classify_role(title):

    title = clean_text(title)

    if "data analyst" in title:
        return "Data Analyst"

    if "data scientist" in title:
        return "Data Scientist"

    if "machine learning" in title or "ml engineer" in title:
        return "ML Engineer"

    if "software engineer" in title:
        return "Software Engineer"

    if "software developer" in title:
        return "Software Developer"

    if "developer" in title:
        return "Developer"

    if "engineer" in title:
        return "Engineer"

    if "manager" in title:
        return "Manager"

    if "designer" in title:
        return "Designer"

    if "analyst" in title:
        return "Analyst"

    if "consultant" in title:
        return "Consultant"

    if "recruiter" in title:
        return "Recruiter"

    if "sales" in title:
        return "Sales"

    return "Other"


df["ROLE"] = df["JOB TITLE"].apply(
    classify_role
)


# ============================================================
# 8. CREATE SKILL CATEGORY LABELS
# ============================================================

SKILL_KEYWORDS = {

    "Programming": [
        "python",
        "java",
        "javascript",
        "c++",
        "c#",
        "programming",
        "developer",
    ],

    "Data and Analytics": [
        "sql",
        "data analysis",
        "analytics",
        "power bi",
        "tableau",
        "excel",
        "data visualization",
        "statistics",
    ],

    "Machine Learning": [
        "machine learning",
        "ml",
        "deep learning",
        "artificial intelligence",
        "tensorflow",
        "pytorch",
        "scikit-learn",
        "nlp",
    ],

    "Cloud and DevOps": [
        "aws",
        "azure",
        "gcp",
        "cloud",
        "docker",
        "kubernetes",
        "devops",
        "terraform",
    ],

    "Engineering": [
        "catia",
        "engineering",
        "automotive",
        "electrical",
        "mechanical",
        "cad",
        "circuit",
    ],

    "Business": [
        "management",
        "sales",
        "marketing",
        "business development",
        "finance",
    ],

    "Human Resources": [
        "recruitment",
        "recruiter",
        "human resources",
        "hr",
        "talent acquisition",
    ],
}


def classify_skill(text):

    text = clean_text(text)

    scores = {}

    for skill_category, keywords in SKILL_KEYWORDS.items():

        score = 0

        for keyword in keywords:

            if keyword in text:
                score += 1

        scores[skill_category] = score

    best_skill = max(
        scores,
        key=scores.get
    )

    if scores[best_skill] == 0:
        return "Other"

    return best_skill


df["SKILL_CATEGORY"] = df["SKILLSETS"].apply(
    classify_skill
)


# ============================================================
# 9. DISPLAY GENERATED LABELS
# ============================================================

print("\n" + "=" * 70)
print("GENERATED TARGET LABELS")
print("=" * 70)

print("\nJOB CATEGORY:")
print(df["JOB_CATEGORY"].value_counts())

print("\nINDUSTRY:")
print(df["INDUSTRY"].value_counts())

print("\nSKILL CATEGORY:")
print(df["SKILL_CATEGORY"].value_counts())

print("\nROLE:")
print(df["ROLE"].value_counts())


# ============================================================
# 10. MODEL CREATION
# ============================================================

MODELS = {

    "Logistic Regression": LogisticRegression(
        max_iter=2000,
        class_weight="balanced"
    ),

    "Random Forest": RandomForestClassifier(
        n_estimators=200,
        random_state=RANDOM_STATE,
        class_weight="balanced"
    ),

    "Naive Bayes": MultinomialNB(),
}


def create_pipeline(model):

    return Pipeline([
        (
            "tfidf",
            TfidfVectorizer(
                lowercase=True,
                stop_words="english",
                ngram_range=(1, 2),
                min_df=1
            )
        ),

        (
            "classifier",
            model
        )
    ])


# ============================================================
# 11. TRAINING FUNCTION
# ============================================================

def train_models(
    task_name,
    X,
    y
):

    print("\n")
    print("=" * 70)
    print(f"TRAINING: {task_name}")
    print("=" * 70)

    y = y.fillna("Unknown").astype(str)

    # Remove empty records
    valid = X.str.strip() != ""

    X = X[valid]
    y = y[valid]

    number_of_classes = y.nunique()

    print(f"Samples : {len(X)}")
    print(f"Classes : {number_of_classes}")

    if number_of_classes < 2:
        print(
            f"Skipping {task_name}: "
            f"at least 2 classes are required."
        )
        return

    # Very small datasets may not support stratified splitting.
    class_counts = y.value_counts()

    can_stratify = (
        len(class_counts) >= 2
        and class_counts.min() >= 2
        and len(X) >= 10
    )

    if can_stratify:

        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=0.25,
            random_state=RANDOM_STATE,
            stratify=y
        )

    else:

        print(
            "Warning: dataset is too small for a reliable "
            "stratified split."
        )

        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=0.25,
            random_state=RANDOM_STATE
        )

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    for model_name, model in MODELS.items():

        print("\n" + "-" * 50)
        print(model_name)
        print("-" * 50)

        pipeline = create_pipeline(model)

        try:

            pipeline.fit(
                X_train,
                y_train
            )

            predictions = pipeline.predict(
                X_test
            )

            accuracy = accuracy_score(
                y_test,
                predictions
            )

            print(
                f"Accuracy: {accuracy:.4f}"
            )

            print("\nClassification Report:")

            print(
                classification_report(
                    y_test,
                    predictions,
                    zero_division=0
                )
            )

            # Save model
            safe_task = task_name.lower().replace(
                " ",
                "_"
            )

            safe_model = model_name.lower().replace(
                " ",
                "_"
            )

            model_path = (
                MODEL_DIR
                / f"{safe_task}_{safe_model}.joblib"
            )

            joblib.dump(
                pipeline,
                model_path
            )

            print(
                f"Saved: {model_path}"
            )

        except Exception as error:

            print(
                f"Could not train {model_name}: {error}"
            )


# ============================================================
# 12. TRAIN ALL CLASSIFIERS
# ============================================================

# ------------------------------------------------------------
# JOB CATEGORY
# ------------------------------------------------------------

train_models(
    task_name="Job Category",
    X=df["TEXT"],
    y=df["JOB_CATEGORY"]
)


# ------------------------------------------------------------
# INDUSTRY
# ------------------------------------------------------------

train_models(
    task_name="Industry",
    X=df["TEXT"],
    y=df["INDUSTRY"]
)


# ------------------------------------------------------------
# SKILL CLASSIFICATION
# ------------------------------------------------------------

train_models(
    task_name="Skill Classification",
    X=df["SKILL_TEXT"],
    y=df["SKILL_CATEGORY"]
)


# ------------------------------------------------------------
# ROLE CLASSIFICATION
# ------------------------------------------------------------

train_models(
    task_name="Role Classification",
    X=df["ROLE_TEXT"],
    y=df["ROLE"]
)


# ============================================================
# 13. SAVE DATASET WITH GENERATED LABELS
# ============================================================

OUTPUT_FILE = Path(
    "data/jobs_with_ml_labels.xlsx"
)

df.to_excel(
    OUTPUT_FILE,
    index=False
)

print("\n" + "=" * 70)
print("TRAINING COMPLETE")
print("=" * 70)

print(
    f"\nDataset with generated labels saved to:"
    f"\n{OUTPUT_FILE}"
)

print(
    f"\nTrained models saved to:"
    f"\n{MODEL_DIR}"
)