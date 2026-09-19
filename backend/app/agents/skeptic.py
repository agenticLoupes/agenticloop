"""Skeptic/Verifier (§9.3) — runs on Jev. 8 Noul checks + a Choice -> SURFACE/DISMISS/VERIFY.

Enforces the evidence contract first: a candidate whose evidence ids don't resolve to real
records of this patient is dropped before any model call. No confidence percentages surface.
"""
from app.jev import judge
from app.models import Candidate, SkepticResult
from app.tools.records import get_record
from app.trace import Trace

NOUL_CHECKS = {
    "same_patient": "Does every evidence record belong to the stated patient?",
    "relevant": "Is this candidate relevant to the stated procedure and tooth context?",
    "current": "Is the information current enough to present as current?",
    "not_contradicted": "Is the candidate free of contradiction by newer evidence in the state?",
    "not_duplicate": "Is this candidate distinct from the other candidates listed?",
    "not_overclaiming": "Does the candidate's summary stay within what the source records support?",
}


def challenge(candidates: list[Candidate], context: dict, trace: Trace) -> list[SkepticResult]:
    if not candidates:
        return []
    trace.add("skeptic", "challenge", f"Challenging {len(candidates)} candidate record(s)")
    results: list[SkepticResult] = []
    resolved_all = []
    for c in candidates:
        recs = [get_record(_infer_type(c, eid), eid) or get_record_any(eid) for eid in c.evidence_ids]
        resolved_all.append([r for r in recs if r])

    for i, cand in enumerate(candidates):
        recs = resolved_all[i]
        # deterministic checks (§9.3 #1-#2, #8): source real, right patient, linkable
        if len(recs) != len(cand.evidence_ids) or any(
                r.patient_id != context["patient_id"] for r in recs):
            results.append(SkepticResult(decision="DISMISS", candidate=cand,
                                         checks={"source_resolvable": 0.0}))
            trace.add("skeptic", "decision", f"Dismissed '{cand.title}' — evidence not resolvable")
            continue

        state = {
            "patient_id": context["patient_id"],
            "procedure": context["procedure"],
            "tooth_number": context.get("tooth_number"),
            "candidate": cand.model_dump(),
            "evidence_records": [r.model_dump(mode="json") for r in recs],
            "other_candidates": [c.title for j, c in enumerate(candidates) if j != i],
        }
        try:
            probs, decision = judge(
                state,
                nouls=NOUL_CHECKS,
                choice_id="decision",
                choice_instructions=(
                    "Decide: SURFACE this record for the dentist's pre-procedure review, "
                    "DISMISS it as not worth an interruption, or VERIFY if potentially relevant "
                    "but current status/context cannot be established. Stale, resolved, or "
                    "long-completed routine history with no documented complication and no "
                    "connection to current risk is DISMISS — the product surfaces narrowly and "
                    "does not interrupt for unremarkable history."),
                choice_criteria=["SURFACE", "DISMISS", "VERIFY"],
            )
        except Exception as e:  # Jev unavailable -> VERIFY, never invent certainty (§22)
            probs, decision = {"provider_error": 0.0}, "VERIFY"
            trace.add("skeptic", "error", f"Verifier unavailable; marking '{cand.title}' VERIFY")

        if decision not in {"SURFACE", "DISMISS", "VERIFY"}:
            decision = "VERIFY"
        results.append(SkepticResult(decision=decision, candidate=cand, checks=probs))
        trace.add("skeptic", "decision", f"{decision.title()}: {cand.title}")
    return results


def _infer_type(c: Candidate, eid: str) -> str:
    prefix = eid.split("-")[0].upper()
    return {"MED": "medication", "ALG": "allergy", "COND": "medical_condition",
            "DENT": "dental_event", "NOTE": "clinical_note", "IMG": "imaging",
            "CONV": "conversation"}.get(prefix, c.record_type)


def get_record_any(eid: str):
    for t in ("medication", "allergy", "medical_condition", "dental_event",
              "clinical_note", "imaging", "conversation", "patient"):
        r = get_record(t, eid)
        if r:
            return r
    return None
