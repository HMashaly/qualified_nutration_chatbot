"""
PostgreSQL helpers for qualified_nutration_chatbot auth and admin data.
Reads credentials from:
  1. Streamlit Cloud secrets (st.secrets) — when running on cloud
  2. .env file / environment variables — local dev
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

import psycopg
from psycopg.rows import dict_row

from typing import Optional

def _get_database_url() -> Optional[str]:
    """Try Streamlit secrets first, then env vars."""
    try:
        import streamlit as st
        url = st.secrets.get("DATABASE_URL")
        if url:
            return url
    except Exception:
        pass
    return os.getenv("DATABASE_URL")


def _get_openai_key():
    """Inject OPENAI_API_KEY from Streamlit secrets into env if needed."""
    if not os.getenv("OPENAI_API_KEY"):
        try:
            import streamlit as st
            key = st.secrets.get("OPENAI_API_KEY")
            if key:
                os.environ["OPENAI_API_KEY"] = key
        except Exception:
            pass


# Inject OpenAI key at import time so LangChain picks it up
_get_openai_key()


def get_connection():
    database_url = _get_database_url()
    if database_url:
        return psycopg.connect(database_url, row_factory=dict_row)

    # Fall back to individual POSTGRES_* variables
    def _req(name):
        v = os.getenv(name)
        if not v:
            raise RuntimeError(f"Missing required environment variable: {name}")
        return v

    return psycopg.connect(
        host=_req("POSTGRES_HOST"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        dbname=_req("POSTGRES_DB"),
        user=_req("POSTGRES_USER"),
        password=_req("POSTGRES_PASSWORD"),
        row_factory=dict_row,
    )


def init_database() -> None:
    schema_path = Path(__file__).resolve().parent / "sql" / "schema.sql"
    sql = schema_path.read_text(encoding="utf-8")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
