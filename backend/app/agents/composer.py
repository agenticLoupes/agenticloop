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
        # imaging evidence renders inline on the card, with its authored description
        image_url = None
        image_caption = None
        for eid in r.candidate.evidence_ids:
            if eid.startswith("IMG"):
                rec = get_record("imaging", eid)
                if rec:
                    image_url = rec.data.get("image_url")
                    meta = rec.data.get("metadata") or {}
                    image_caption = meta.get("description")
                break
        cards.append(Card(
            decision=r.decision,
            title=f"{TITLES[r.decision]} — {r.candidate.title}",
            summary=r.candidate.summary,
            reason_shown=r.candidate.reason or "Selected during pre-procedure record review.",
            evidence_ids=r.candidate.evidence_ids,
            image_url=image_url,
            image_caption=image_caption,
        ))
    trace.add("composer", "cards", f"Prepared {len(cards)} evidence-backed card(s)")
    return cards


def _plural(n: int, singular: str, plural: str | None = None) -> str:
    """'1 record' / '2 records' — reads like a sentence, not a form field."""
    return f"{n} {singular if n == 1 else (plural or singular + 's')}"


def summarize(state, tool_calls: int) -> str:
    """Deterministic safe-language recap — no model call, no advice, no invention (§21)."""
    intent = state.procedure.replace("_", " ")
    if state.tooth_number is not None:
        intent += f" at tooth #{state.tooth_number}"
    surfaced = [c for c in state.final_cards if c.decision == "SURFACE"]
    verify = [c for c in state.final_cards if c.decision == "VERIFY"]
    parts = [f"Guardian checked {_plural(tool_calls, 'record source')} before the planned {intent}."]
    if surfaced:
        names = "; ".join(c.title.split("— ", 1)[-1] for c in surfaced)
        parts.append(f"{_plural(len(surfaced), 'record')} worth your review: {names}.")
    if verify:
        names = "; ".join(c.title.split("— ", 1)[-1] for c in verify)
        parts.append(
            f"{_plural(len(verify), 'item')} could not be confirmed as current and need verifying: {names}."
        )
    if state.dismissed_count:
        parts.append(
            f"{_plural(state.dismissed_count, 'possible finding')} "
            f"{'was' if state.dismissed_count == 1 else 'were'} ruled out after a second look."
        )
    if not state.final_cards:
        parts.append("No record deserved an interruption; silence is the result.")
    parts.append("You remain the decision-maker; every item links to its source record.")
    return " ".join(parts)

