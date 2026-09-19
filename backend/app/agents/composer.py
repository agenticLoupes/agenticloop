"""Assist Composer (§9.4) — formatting, not medical reasoning. Safe language only (§21)."""
from app.models import Card, SkepticResult
from app.tools.records import get_record
from app.trace import Trace

TITLES = {"SURFACE": "Record to review", "VERIFY": "Item to verify"}


def compose(results: list[SkepticResult], trace: Trace) -> list[Card]:
    cards: list[Card] = []
    for r in results:
        if r.decision not in TITLES:
            continue
        if not r.candidate.evidence_ids:  # NO EVIDENCE ID -> NO FACTUAL CARD (§12)
            continue
        # imaging evidence renders inline on the card
        image_url = None
        for eid in r.candidate.evidence_ids:
            if eid.startswith("IMG"):
                rec = get_record("imaging", eid)
                if rec:
                    image_url = rec.data.get("image_url")
                break
        cards.append(Card(
            decision=r.decision,
            title=f"{TITLES[r.decision]} — {r.candidate.title}",
            summary=r.candidate.summary,
            reason_shown=r.candidate.reason or "Selected during pre-procedure record review.",
            evidence_ids=r.candidate.evidence_ids,
            image_url=image_url,
        ))
    trace.add("composer", "cards", f"Prepared {len(cards)} evidence-backed card(s)")
    return cards


def summarize(state, tool_calls: int) -> str:
    """Deterministic safe-language recap — no model call, no advice, no invention (§21)."""
    intent = state.procedure.replace("_", " ")
    if state.tooth_number is not None:
        intent += f" at tooth #{state.tooth_number}"
    surfaced = [c for c in state.final_cards if c.decision == "SURFACE"]
    verify = [c for c in state.final_cards if c.decision == "VERIFY"]
    parts = [f"Guardian investigated {tool_calls} record source(s) before the planned {intent}."]
    if surfaced:
        names = "; ".join(c.title.split("— ", 1)[-1] for c in surfaced)
        parts.append(f"{len(surfaced)} record(s) surfaced for review: {names}.")
    if verify:
        names = "; ".join(c.title.split("— ", 1)[-1] for c in verify)
        parts.append(f"{len(verify)} item(s) could not be established as current and require verification: {names}.")
    if state.dismissed_count:
        parts.append(f"{state.dismissed_count} candidate(s) were dismissed after challenge.")
    if not state.final_cards:
        parts.append("No record deserved an interruption; silence is the result.")
    parts.append("The dentist remains the decision-maker; every item links to its source record.")
    return " ".join(parts)

