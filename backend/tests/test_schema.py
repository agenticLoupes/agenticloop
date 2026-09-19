from app.db import get_conn

EXPECTED_TABLES = {
    "patient", "dental_event", "medical_condition", "medication", "allergy",
    "clinical_note", "investigation_run", "agent_event",
    "imaging_study", "conversation_transcript",
}

KEY_COLUMNS = [
    ("patient", "demo_identifier"),
    ("dental_event", "tooth_number"),
    ("medication", "medication_name"),
    ("medication", "status"),
    ("allergy", "substance"),
    ("clinical_note", "summary"),
    ("imaging_study", "region_label"),
    ("imaging_study", "image_url"),
    ("conversation_transcript", "transcript_text"),
    ("agent_event", "sequence_no"),
]


def test_all_tables_exist():
    with get_conn() as c:
        rows = c.execute(
            "select table_name from information_schema.tables where table_schema='public'"
        ).fetchall()
    names = {r["table_name"] for r in rows}
    missing = EXPECTED_TABLES - names
    assert not missing, f"missing tables: {missing}"


def test_key_columns_present():
    with get_conn() as c:
        rows = c.execute(
            "select table_name, column_name from information_schema.columns where table_schema='public'"
        ).fetchall()
    have = {(r["table_name"], r["column_name"]) for r in rows}
    missing = [f"{t}.{col}" for t, col in KEY_COLUMNS if (t, col) not in have]
    assert not missing, f"missing columns: {missing}"
