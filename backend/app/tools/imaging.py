"""Imaging tools. get_imaging is deterministic (Phase 1); read_imaging (vision) lands in Phase 2."""
from typing import Optional

from app.db import get_conn
from app.tools.records import _to_record
from app.models import Record


def get_imaging(patient_id: str, tooth_number: Optional[int] = None) -> list[Record]:
    sql = "select * from imaging_study where patient_id = %s"
    params: list = [patient_id]
    if tooth_number is not None:
        sql += " and tooth_number = %s"
        params.append(tooth_number)
    sql += " order by recorded_at desc nulls last"
    with get_conn() as c:
        rows = c.execute(sql, tuple(params)).fetchall()
    return [_to_record(r, "imaging") for r in rows]
