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


class Candidate(BaseModel):
    """Guardian's proposal: a record that may deserve the dentist's review."""
    title: str
    summary: str
    record_type: str
    evidence_ids: list[str]
    reason: str  # why the Guardian selected it (pattern/context), never advice


class SkepticResult(BaseModel):
    decision: str  # SURFACE | DISMISS | VERIFY
    candidate: Candidate
    checks: dict[str, float] = {}  # the 8 Noul probabilities (internal; never shown as %)


class Card(BaseModel):
    """Evidence-backed UI card (§9.4/§12). NO EVIDENCE ID -> NO FACTUAL CARD."""
    decision: str  # SURFACE | VERIFY
    title: str
    summary: str
    reason_shown: str
    evidence_ids: list[str]


class InvestigationState(BaseModel):
    """Explicit application state (§13) — never hidden conversation history."""
    run_id: str
    patient_id: str
    procedure: str
    tooth_number: Optional[int] = None
    investigation_goal: str = "pre_procedure_review"
    tool_calls: list[dict] = []
    observations: list[dict] = []
    candidate_evidence: list[Candidate] = []
    skeptic_results: list[SkepticResult] = []
    final_cards: list[Card] = []
    dismissed_count: int = 0
    verify_count: int = 0
    status: str = "running"  # running | complete | error
    error: Optional[str] = None
