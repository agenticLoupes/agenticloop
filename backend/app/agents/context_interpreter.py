"""Context Interpreter (§9.1) — normalize intent, flag missing context, never invent facts.

Input is already structured (dropdowns), so this is deterministic code, not an LLM call.
"""
from app.tools.records import get_patient_summary

TOOTH_REQUIRED = {"extraction", "root_canal", "crown", "filling", "implant"}


def interpret(patient_id: str, procedure: str, tooth_number: int | None) -> dict:
    """Returns {ok, context?, error?} per the failure table (§22)."""
    if not patient_id or get_patient_summary(patient_id) is None:
        return {"ok": False, "error": "patient_not_found"}
    proc = (procedure or "").lower().strip().replace(" ", "_")
    if not proc:
        return {"ok": False, "error": "procedure_required"}
    if proc in TOOTH_REQUIRED and tooth_number is None:
        return {"ok": False, "error": "tooth_number_required"}
    return {"ok": True, "context": {"patient_id": patient_id, "procedure": proc,
                                    "tooth_number": tooth_number}}
