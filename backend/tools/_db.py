"""Minimal SQLite access for the C-lane tools. [OWNER: C]

A1's clients/db.py is the long-term home; until it merges this opens DB_PATH
directly and bootstraps ../db/schema.sql + ../db/seed.sql on an empty file so
the tools and tests run standalone.
"""
from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

_DB_DIR = Path(__file__).resolve().parents[2] / "db"


def db_path() -> str:
    return os.environ.get("DB_PATH", "./loupes.db")


def connect() -> sqlite3.Connection:
    path = db_path()
    fresh = not Path(path).exists() or Path(path).stat().st_size == 0
    conn = sqlite3.connect(path, timeout=5)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    if fresh:
        conn.executescript((_DB_DIR / "schema.sql").read_text())
        conn.executescript((_DB_DIR / "seed.sql").read_text())
        conn.commit()
    return conn


def rows(cur: sqlite3.Cursor) -> list[dict]:
    return [dict(r) for r in cur.fetchall()]


def loads(s: str | None, default):
    try:
        return json.loads(s) if s else default
    except json.JSONDecodeError:
        return default
