"""Postgres connection pool (Supabase session pooler).

Fresh connections cost ~5-8s here (flaky local DNS + TLS to us-west-2), which made
every screen feel stuck. Fixes: resolve the host to an IP once (hostaddr skips DNS
per connection) and keep a pre-warmed pool so requests reuse open connections.
"""
import socket
from contextlib import contextmanager
from functools import lru_cache
from urllib.parse import urlparse

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from app.config import get_settings


def _conninfo() -> str:
    url = get_settings().supabase_db_url
    try:  # resolve once; skip per-connection DNS (the flaky part)
        host = urlparse(url).hostname
        ip = socket.getaddrinfo(host, 5432, socket.AF_INET)[0][4][0]
        sep = "&" if "?" in url else "?"
        return f"{url}{sep}hostaddr={ip}&connect_timeout=10"
    except OSError:
        return url  # DNS down right now — let psycopg try normally


@lru_cache
def _pool() -> ConnectionPool:
    return ConnectionPool(
        _conninfo(),
        min_size=3,  # pre-warmed; investigation polling reuses these
        max_size=6,
        kwargs={"row_factory": dict_row},
        timeout=15,  # fail fast instead of hanging the UI (§22: recoverable demo error)
    )


@contextmanager
def get_conn():
    with _pool().connection() as conn:
        yield conn
