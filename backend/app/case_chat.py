"""Case briefing chat for the dentist — every investigation, this patient only.

Explains the record and the completed review so the dentist can analyse the case.
Never diagnoses, never recommends treatment. Facts come from tools, not the model.
"""
from __future__ import annotations

import json
import re

from langchain_core.messages import HumanMessage, SystemMessage

from app.db import get_conn
from app.provider import get_llm
from app.tools import conversations, imaging, records

ASK_SYSTEM = """You are a case-briefing assistant for a dentist using LOUPEIN.
You help them understand THIS patient's synthetic record and the completed pre-procedure
review so they can analyse the case themselves.

You may ONLY use the CASE DATA provided (patient records + investigation cards/trace).
Rules, non-negotiable:
- Explain WHAT is on file, WHY a record was surfaced/dismissed/marked verify, and WHERE
  each fact came from. Cite evidence ids like (MED-018) whenever you state a fact.
- NEVER diagnose, recommend treatment, suggest what to do clinically, or prescribe.
  If asked for a clinical decision or what to do next, reply exactly:
  "I can explain what is on file and what the review found, but clinical decisions and
  treatment choices remain with you as the dentist."
- If the answer is not in the provided data, say the record/review did not establish it.
- Keep answers to a few sentences. The data is synthetic prototype data.
- Do not mention other patients. This briefing is only for the listed patient."""


class CaseChatNotFound(Exception):
    pass


class CaseChatUnavailable(Exception):
    pass


class EmptyQuestion(Exception):
    pass


_REFUSAL = (
    "I can explain what is on file and what the review found, but clinical decisions and "
    "treatment choices remain with you as the dentist."
)
_ADVICE = re.compile(
    r"\b(you should|you must|i recommend|i advise|prescribe|treatment plan|"
    r"go ahead and extract|do not extract|do not proceed)\b",
    re.I,
)


def _dump(rs) -> list[dict]:
    return [r.model_dump(mode="json") for r in rs]


def _index_briefing(briefing: dict) -> dict[str, dict]:
    idx: dict[str, dict] = {}
    patient = briefing.get("patient")
    if patient and patient.get("record_id"):
        idx[patient["record_id"]] = patient
    for key in (
        "medications", "allergies", "conditions", "dental_events",
        "notes", "conversations", "imaging",
    ):
        for rec in briefing.get(key) or []:
            rid = rec.get("record_id")
            if rid:
                idx[rid] = rec
    return idx


def _sanitize_answer(text: str) -> str:
    cleaned = text.strip()
    return _REFUSAL if _ADVICE.search(cleaned) else cleaned


def patient_briefing(patient_id: str) -> dict:
    """Longitudinal snapshot of one patient's own records — used for every case."""
    patient = records.get_patient_summary(patient_id)
    if patient is None:
        raise CaseChatNotFound("patient not found")
    notes = records.get_clinical_notes(patient_id)
    return {
        "patient": patient.model_dump(mode="json"),
        "medications": _dump(records.get_medication_history(patient_id)),
        "allergies": _dump(records.get_allergies(patient_id)),
        "conditions": _dump(records.get_medical_conditions(patient_id)),
        "dental_events": _dump(records.get_dental_history(patient_id)),
        "notes": _dump(notes),
        "conversations": _dump(conversations.list_conversations(patient_id)),
        "imaging": _dump(imaging.get_imaging(patient_id)),
    }


def answer_case_question(
    run_id: str,
    question: str,
    history: list[dict] | None = None,
) -> dict:
    question = (question or "").strip()
    if not question:
        raise EmptyQuestion("question required")
    if len(question) > 800:
        raise EmptyQuestion("question too long")

    with get_conn() as c:
        row = c.execute(
            "select id, patient_id, procedure, tooth_number, status, result"
            " from investigation_run where id=%s",
            (run_id,),
        ).fetchone()
        if not row or row["status"] != "complete" or not row["result"]:
            raise CaseChatNotFound("run not found or incomplete")
        trace_rows = c.execute(
            "select agent, summary from agent_event where run_id=%s order by sequence_no",
            (run_id,),
        ).fetchall()

    result = row["result"]
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except json.JSONDecodeError as e:
            raise CaseChatUnavailable("corrupt investigation result") from e
    briefing = patient_briefing(row["patient_id"])
    by_id = _index_briefing(briefing)

    evidence = {}
    for card in result.get("final_cards") or []:
        for eid in card.get("evidence_ids") or []:
            rec = by_id.get(eid)
            if rec and rec.get("patient_id") == row["patient_id"]:
                evidence[eid] = rec

    turns = []
    for t in (history or [])[-8:]:
        role = t.get("role")
        content = (t.get("content") or "").strip()
        if role in ("dentist", "assistant") and content:
            turns.append({"role": role, "content": content[:1200]})

    packed = json.dumps(
        {
            "patient_id": row["patient_id"],
            "procedure": result.get("procedure") or row["procedure"],
            "tooth_number": result.get("tooth_number") if result.get("tooth_number") is not None
            else row["tooth_number"],
            "investigation_summary": result.get("summary"),
            "cards": result.get("final_cards"),
            "dismissed_count": result.get("dismissed_count"),
            "verify_count": result.get("verify_count"),
            "skeptic_results": [
                {
                    "decision": s.get("decision"),
                    "title": (s.get("candidate") or {}).get("title"),
                    "reason": (s.get("candidate") or {}).get("reason"),
                }
                for s in (result.get("skeptic_results") or [])
            ],
            "trace": [f"{t['agent']}: {t['summary']}" for t in trace_rows],
            "evidence_records": evidence,
            "patient_record": briefing,
            "prior_turns": turns,
        },
        default=str,
    )

    try:
        out = get_llm().invoke(
            [
                SystemMessage(content=ASK_SYSTEM),
                HumanMessage(
                    content=f"CASE DATA:\n{packed}\n\nDENTIST'S QUESTION: {question}"
                ),
            ]
        )
        text = out.content
        if isinstance(text, list):
            text = "\n".join(
                p.get("text", "") if isinstance(p, dict) else str(p) for p in text
            )
        return {"answer": _sanitize_answer(str(text))}
    except Exception as e:
        raise CaseChatUnavailable(str(e)) from e
