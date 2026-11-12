
import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return psycopg.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", "5432"),
        dbname=os.getenv("PGDATABASE", "job_analysis_db"),
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD"),
    )