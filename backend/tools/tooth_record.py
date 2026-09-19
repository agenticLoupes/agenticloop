"""get_tooth_record(tooth, patient_id) -> ToothRecord dict.  [OWNER: C]  Never cut.

Accepts FDI ('36') or Universal ('19', 'nineteen'); everything stored is FDI.
"""
from __future__ import annotations

from numbering import is_fdi, parse_tooth
from tools._db import connect, loads, rows


def normalize_tooth(tooth: str) -> str:
    t = str(tooth).strip()
    if t.isdigit() and is_fdi(t) and not (1 <= int(t) <= 32):
        return t
    parsed = parse_tooth(t)
    if parsed is None:
        raise ValueError(f"unrecognized tooth: {tooth!r}")
    return parsed


def get_tooth_record(tooth: str, patient_id: str) -> dict:
    fdi = normalize_tooth(tooth)
    conn = connect()
    try:
        row = conn.execute(
            "SELECT * FROM teeth WHERE patient_id=? AND tooth=?", (patient_id, fdi)
        ).fetchone()
        patient = conn.execute(
            "SELECT allergies FROM patients WHERE id=?", (patient_id,)
        ).fetchone()
        findings = rows(conn.execute(
            "SELECT id, session_id, observation, source, confidence, created_at "
            "FROM session_findings WHERE patient_id=? AND tooth=? "
            "ORDER BY created_at DESC, id DESC LIMIT 10", (patient_id, fdi)))
        perio = rows(conn.execute(
            "SELECT periodontal_depth_mm, measured_on FROM perio_history "
            "WHERE patient_id=? AND tooth=? ORDER BY measured_on", (patient_id, fdi)))
    finally:
        conn.close()

    base = dict(row) if row else {"restoration": None, "periodontal_depth_mm": None,
                                  "last_treated": None, "notes": None}
    return {
        "patient_id": patient_id,
        "tooth": fdi,
        "restoration": base["restoration"],
        "periodontal_depth_mm": base["periodontal_depth_mm"],
        "last_treated": base["last_treated"],
        "notes": base["notes"],
        "recent_findings": findings,
        "perio_history": perio,
        "patient_allergies": loads(patient["allergies"], []) if patient else [],
        "found": row is not None,
    }
