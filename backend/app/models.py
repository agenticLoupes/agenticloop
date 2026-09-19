"""Core data models. Record is the evidence primitive (spec §11/§12)."""
from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel


class Record(BaseModel):
    """A single synthetic source record. Its record_id is the evidence id (§12)."""
    record_id: str
    record_type: str
    patient_id: str
    source_label: Optional[str] = None
    recorded_at: Optional[date | datetime] = None
    data: dict[str, Any] = {}
