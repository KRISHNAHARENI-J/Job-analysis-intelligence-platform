
import json
from pathlib import Path

import pandas as pd
from docx import Document
from psycopg.types.json import Jsonb

from db_connection import get_connection

BASE_DIR = Path(__file__).resolve().parent

# Change these filenames if your actual names differ.
EXCEL_FILES = {
    "job_dataset": "job_dataset.xlsx",
    "jobs_with_nlp": "jobs_with_nlp.xlsx",
    "annotated_job_training_dataset":
        "annotated_job_training_dataset.xlsx",
}


def import_excel(table_name, filename):
    path = BASE_DIR / filename
    df = pd.read_excel(path)

    # Convert Excel values into JSON-compatible records.
    records = json.loads(
        df.to_json(orient="records", date_format="iso")
    )

    with get_connection() as conn:
        with conn.cursor() as cur:
            for record in records:
                cur.execute(
                    f"INSERT INTO {table_name} (data) VALUES (%s)",
                    (Jsonb(record),),
                )

    print(f"{table_name}: imported {len(records)} rows")


def import_json():
    path = BASE_DIR / "llm_output.json"

    with open(path, "r", encoding="utf-8") as file:
        content = json.load(file)

    # Keep the entire JSON structure in one row.
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO llm_output (data) VALUES (%s)",
                (Jsonb(content),),
            )

    print("llm_output: imported JSON content")


def import_word_document():
    path = BASE_DIR / "mlmodel_output.docx"
    doc = Document(path)

    content = {
        "paragraphs": [
            p.text for p in doc.paragraphs if p.text.strip()
        ],
        "tables": [
            [
                [cell.text for cell in row.cells]
                for row in table.rows
            ]
            for table in doc.tables
        ],
    }

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO mlmodel_output (data) VALUES (%s)",
                (Jsonb(content),),
            )

    print("mlmodel_output: imported document text and tables")


if __name__ == "__main__":
    for table_name, filename in EXCEL_FILES.items():
        import_excel(table_name, filename)

    import_json()
    import_word_document()

    print("Import completed.")