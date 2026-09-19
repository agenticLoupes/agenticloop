"""log_finding(...) -> {"id": int}   [OWNER: C]

Called AUTONOMOUSLY by the agent after every exchange. Writes the row in
session_findings that makes this an agent instead of a chatbot (plan §1).
"""
from __future__ import annotations

from tools._db import connect
from tools.tooth_record import normalize_tooth

SOURCES = ("cv", "dentist_speech", "patient_speech", "agent")


def log_finding(tooth: str, observation: str, source: str, confidence: float,
                session_id: str, patient_id: str) -> dict:
    if source not in SOURCES:
        raise ValueError(f"source must be one of {SOURCES}, got {source!r}")
    fdi = normalize_tooth(tooth)
    conn = connect()
    try:
        cur = conn.execute(
            "INSERT INTO session_findings (session_id, patient_id, tooth, observation, source, confidence) "
            "VALUES (?,?,?,?,?,?)",
            (session_id, patient_id, fdi, observation.strip(), source, float(confidence)))
        conn.commit()
        return {"id": cur.lastrowid, "tooth": fdi}
    finally:
        conn.close()
