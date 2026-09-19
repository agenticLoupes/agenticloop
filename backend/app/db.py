"""Postgres connection helper (Supabase session pooler)."""
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

from app.config import get_settings


@contextmanager
def get_conn():
    # ponytail: one direct connection per use; add pooling only if concurrency demands it
    with psycopg.connect(get_settings().supabase_db_url, row_factory=dict_row) as conn:
        yield conn
