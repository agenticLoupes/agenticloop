"""Investigation pipeline: interpreter -> guardian (ReAct loop) -> skeptic (Jev) -> composer.

Explicit application state (§13); trace persisted throughout; fail-safe per §22.
"""
import json
import uuid

from app.agents import composer, context_interpreter, guardian, skeptic
from app.db import get_conn
from app.models import InvestigationState
from app.trace import Trace


def start_run(patient_id: str, procedure: str, tooth_number: int | None):
    """Validate context and create the run row. Returns (run_id, ctx) or (None, error)."""
    parsed = context_interpreter.interpret(patient_id, procedure, tooth_number)
    if not parsed["ok"]:
        return None, parsed["error"]
    ctx = parsed["context"]
    with get_conn() as c:
        row = c.execute(
            "insert into investigation_run (patient_id, procedure, tooth_number, status)"
            " values (%s,%s,%s,'running') returning id",
            (ctx["patient_id"], ctx["procedure"], ctx["tooth_number"]),
        ).fetchone()
        c.commit()
    return str(row["id"]), ctx


def execute_run(run_id: str, ctx: dict) -> InvestigationState:
    """Run the agent pipeline for an already-created run (sync; callable in background)."""
    trace = Trace(run_id)
    trace.add("context_interpreter", "context", f"Procedure: {ctx['procedure']}"
              + (f", tooth #{ctx['tooth_number']}" if ctx["tooth_number"] is not None else ""))

    state = InvestigationState(run_id=run_id, **ctx)
    try:
        state.candidate_evidence = guardian.investigate(ctx, trace)
        state.skeptic_results = skeptic.challenge(state.candidate_evidence, ctx, trace)
        state.final_cards = composer.compose(state.skeptic_results, trace)
        state.dismissed_count = sum(1 for r in state.skeptic_results if r.decision == "DISMISS")
        state.verify_count = sum(1 for r in state.skeptic_results if r.decision == "VERIFY")
        tool_calls = sum(1 for e in trace.events
                         if e["agent"] == "guardian" and e["event_type"] == "tool_call")
        state.summary = composer.summarize(state, tool_calls)
        state.status = "complete"
    except Exception as e:  # fail safely: recoverable demo error, never invented results (§22)
        state.status = "error"
        state.error = f"provider_error: {e}"
        trace.add("system", "error", "Investigation failed safely; no unsupported result shown")

    with get_conn() as c:
        c.execute(
            "update investigation_run set status=%s, result=%s, completed_at=now() where id=%s",
            (state.status, json.dumps(state.model_dump(mode="json")), run_id),
        )
        c.commit()
    return state


def run_investigation(patient_id: str, procedure: str, tooth_number: int | None) -> InvestigationState:
    """Synchronous convenience wrapper (scripts/tests)."""
    run_id, ctx_or_err = start_run(patient_id, procedure, tooth_number)
    if run_id is None:
        return InvestigationState(run_id="", patient_id=patient_id or "", procedure=procedure or "",
                                  tooth_number=tooth_number, status="error", error=ctx_or_err)
    return execute_run(run_id, ctx_or_err)
