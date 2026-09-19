"""Conversation-transcript evidence source. Deterministic ILIKE search over synthetic transcripts."""
from app.db import get_conn
from app.tools.records import _to_record
from app.models import Record


def search_conversations(patient_id: str, query: str, from_date=None, to_date=None) -> list[Record]:
    # ponytail: naive ILIKE over text+summary; swap for FTS if recall matters
    sql = "select * from conversation_transcript where patient_id = %s and (transcript_text ilike %s or summary ilike %s)"
    pattern = f"%{query}%"
    params: list = [patient_id, pattern, pattern]
    if from_date:
        sql += " and transcript_date >= %s"
        params.append(from_date)
    if to_date:
        sql += " and transcript_date <= %s"
        params.append(to_date)
    sql += " order by transcript_date desc nulls last"
    with get_conn() as c:
        rows = c.execute(sql, tuple(params)).fetchall()
    return [_to_record(r, "conversation") for r in rows]
