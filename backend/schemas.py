"""SHARED CONTRACT between frontend and backend. Frozen 2026-09-19 14:45 CDT.

Mirror of frontend/src/api.js. Change one, change both, in the same PR.

Transport is plain HTTP, not a duplex WebSocket:
  POST /frame   browser pushes the newest camera JPEG (1-2 FPS)
  POST /turn    browser sends a wake-word-gated transcript; backend answers
  GET  /flags   browser polls every 2s; unprompted flags appear here
  GET  /health  liveness

Voice runs in the browser (Web Speech API in, speechSynthesis out), so no
audio ever crosses this boundary. The backend only sees text and frames.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Severity = Literal["info", "watch", "stop"]
Source = Literal["cv", "dentist_speech", "patient_speech", "agent"]


class Box(BaseModel):
    """One detected tooth. Coords normalized 0-1, origin top-left."""

    tooth: str = Field(description="FDI number as text, e.g. '36'. 'unknown' if unreadable.")
    x: float
    y: float
    w: float
    h: float
    conf: float = Field(ge=0, le=1)
    highlight: bool = False
    label: str = ""


class Flag(BaseModel):
    """An unprompted alert raised by reconcile(). The only sanctioned interruption."""

    id: int
    tooth: str
    severity: Severity
    message: str
    basis: list[str] = Field(default_factory=list, description="citations, e.g. 'finding:12', 'history:2026-03-02'")
    created_at: str
    spoken: bool = False


# ---- POST /frame -----------------------------------------------------------
class FrameIn(BaseModel):
    session_id: str
    data: str = Field(description="base64 JPEG, no data: prefix")
    ts: int


class FrameOut(BaseModel):
    ok: bool = True


# ---- POST /turn ------------------------------------------------------------
class TurnIn(BaseModel):
    session_id: str
    patient_id: str
    transcript: str = Field(description="wake phrase already stripped by the browser")
    speaker: Literal["dentist", "patient"] = "dentist"


class TurnOut(BaseModel):
    reply: str = Field(description="text for speechSynthesis; empty string means say nothing")
    boxes: list[Box] = Field(default_factory=list)
    findings_logged: int = 0
    flag: Flag | None = None
    latency_ms: int


# ---- GET /flags?session_id=...&since=<id> ----------------------------------
class FlagsOut(BaseModel):
    flags: list[Flag]


# ---- tool return shapes (backend-internal, kept here so A and C agree) ------
class ToothRecord(BaseModel):
    patient_id: str
    tooth: str
    restoration: str | None
    periodontal_depth_mm: int | None
    last_treated: str | None
    notes: str | None
    recent_findings: list[dict]
    patient_allergies: list[str]
