"""Deterministic record tools (spec §11). The ONLY code that reads patient rows.

The LLM never invents patient facts — every fact originates here, carrying a record_id.
"""
from typing import Optional

from app.db import get_conn
from app.models import Record

# record_type -> (table, recorded_at column, default source_label)
TYPE_CONFIG = {
    "patient": ("patient", "created_at", "Synthetic patient record"),
    "dental_event": ("dental_event", "event_date", "Synthetic dental record"),
    "medical_condition": ("medical_condition", "recorded_at", "Synthetic condition record"),
    "medication": ("medication", "recorded_at", "Synthetic medication record"),
    "allergy": ("allergy", "recorded_at", "Synthetic allergy record"),
    "clinical_note": ("clinical_note", "note_date", "Synthetic clinical note"),
    "imaging": ("imaging_study", "recorded_at", "Synthetic radiograph"),
    "conversation": ("conversation_transcript", "transcript_date", "Synthetic conversation transcript"),
}


def _to_record(row: dict, record_type: str) -> Record:
    _table, dtcol, default_label = TYPE_CONFIG[record_type]
    patient_id = row["id"] if record_type == "patient" else row["patient_id"]
    return Record(
        record_id=row["id"],
        record_type=record_type,
        patient_id=patient_id,
        source_label=row.get("source_label") or default_label,
        recorded_at=row.get(dtcol),
        data=dict(row),
    )


def get_record(record_type: str, record_id: str) -> Optional[Record]:
    cfg = TYPE_CONFIG.get(record_type)
    if not cfg:
        return None
    table = cfg[0]
    with get_conn() as c:
        row = c.execute(f"select * from {table} where id = %s", (record_id,)).fetchone()
    return _to_record(row, record_type) if row else None


def get_patient_summary(patient_id: str) -> Optional[Record]:
    with get_conn() as c:
        row = c.execute("select * from patient where id = %s", (patient_id,)).fetchone()
    return _to_record(row, "patient") if row else None


def get_dental_history(patient_id: str, tooth_number: Optional[int] = None,
                       event_types: Optional[list[str]] = None) -> list[Record]:
    sql = "select * from dental_event where patient_id = %s"
    params: list = [patient_id]
    if tooth_number is not None:
        sql += " and tooth_number = %s"
        params.append(tooth_number)
    if event_types:
        sql += " and event_type = any(%s)"
        params.append(list(event_types))
    sql += " order by event_date desc nulls last"
    with get_conn() as c:
        rows = c.execute(sql, tuple(params)).fetchall()
    return [_to_record(r, "dental_event") for r in rows]


def get_active_medications(patient_id: str) -> list[Record]:
    with get_conn() as c:
        rows = c.execute(
            "select * from medication where patient_id = %s and status = 'active' order by recorded_at desc nulls last",
            (patient_id,),
        ).fetchall()
    return [_to_record(r, "medication") for r in rows]


def get_medication_history(patient_id: str, medication_name: Optional[str] = None) -> list[Record]:
    sql = "select * from medication where patient_id = %s"
    params: list = [patient_id]
    if medication_name:
        sql += " and medication_name = %s"
        params.append(medication_name)
    sql += " order by recorded_at desc nulls last"
    with get_conn() as c:
        rows = c.execute(sql, tuple(params)).fetchall()
    return [_to_record(r, "medication") for r in rows]


def get_allergies(patient_id: str) -> list[Record]:
    with get_conn() as c:
        rows = c.execute("select * from allergy where patient_id = %s", (patient_id,)).fetchall()
    return [_to_record(r, "allergy") for r in rows]


def get_medical_conditions(patient_id: str, status: Optional[str] = None) -> list[Record]:
    sql = "select * from medical_condition where patient_id = %s"
    params: list = [patient_id]
    if status:
        sql += " and status = %s"
        params.append(status)
    with get_conn() as c:
        rows = c.execute(sql, tuple(params)).fetchall()
    return [_to_record(r, "medical_condition") for r in rows]


def search_clinical_notes(patient_id: str, query: str, from_date=None, to_date=None) -> list[Record]:
    # ponytail: naive ILIKE search; swap for FTS if recall matters
    sql = "select * from clinical_note where patient_id = %s and summary ilike %s"
    params: list = [patient_id, f"%{query}%"]
    if from_date:
        sql += " and note_date >= %s"
        params.append(from_date)
    if to_date:
        sql += " and note_date <= %s"
        params.append(to_date)
    sql += " order by note_date desc nulls last"
    with get_conn() as c:
        rows = c.execute(sql, tuple(params)).fetchall()
    return [_to_record(r, "clinical_note") for r in rows]
