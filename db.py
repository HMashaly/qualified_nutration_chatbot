"""
PostgreSQL helpers for qualified_nutration_chatbot auth and admin data.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
import psycopg
from psycopg.rows import dict_row

load_dotenv()


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def get_connection():
    # Try DATABASE_URL first (Neon style)
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return psycopg.connect(database_url, row_factory=dict_row)
    
    # Fall back to individual POSTGRES_* variables
    return psycopg.connect(
        host=_required_env("POSTGRES_HOST"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        dbname=_required_env("POSTGRES_DB"),
        user=_required_env("POSTGRES_USER"),
        password=_required_env("POSTGRES_PASSWORD"),
        row_factory=dict_row,
    )


def init_database() -> None:
    schema_path = Path(__file__).resolve().parent / "sql" / "schema.sql"
    sql = schema_path.read_text(encoding="utf-8")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()