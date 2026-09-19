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
    image_url: Optional[str] = None  # set when the evidence is an imaging record (inline render)
    image_caption: Optional[str] = None  # authored description of the image (safe language)


class Citation(BaseModel):
    """An external source the dentist can open (PubMed record or guideline page)."""
    citation_id: str  # "PMID:12345678" or a URL
    label: str = ""
    url: Optional[str] = None


class PatientContextItem(BaseModel):
    """A retrieved patient fact, carrying the record ids it came from (§12)."""
    finding: str
    evidence_ids: list[str] = []


class Approach(BaseModel):
    """A documented approach, never an instruction. NO CITATION -> NOT AN APPROACH."""
    approach: str
    rationale: str = ""
    patient_specific_considerations: list[str] = []
    citations: list[str] = []


class AdvisorAnswer(BaseModel):
    """The Advisor's reply to a dentist-asked question (§9.4 language rules apply)."""
    question: str
    patient_id: Optional[str] = None
    procedure: Optional[str] = None
    tooth_number: Optional[int] = None
    question_focus: str = ""
    patient_context: list[PatientContextItem] = []
    approaches: list[Approach] = []
    cautions: list[str] = []
    patient_communication: str = ""
    urgent_referral: bool = False
    citations: list[Citation] = []
    unavailable_sources: list[str] = []
    notes: str = ""  # free text when the model could not fill the structure (never invented)
    trace: list[dict] = []  # observable tool activity for this answer (§20)
    status: str = "complete"  # complete | error
    error: Optional[str] = None


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
    summary: str = ""  # safe-language recap of the investigation (no advice)
    status: str = "running"  # running | complete | error
    error: Optional[str] = None
