"""Assist Composer (§9.4) — formatting, not medical reasoning. Safe language only (§21)."""
from app.models import Card, SkepticResult
from app.trace import Trace

TITLES = {"SURFACE": "Record to review", "VERIFY": "Item to verify"}


def compose(results: list[SkepticResult], trace: Trace) -> list[Card]:
    cards: list[Card] = []
    for r in results:
        if r.decision not in TITLES:
            continue
        if not r.candidate.evidence_ids:  # NO EVIDENCE ID -> NO FACTUAL CARD (§12)
            continue
        cards.append(Card(
            decision=r.decision,
            title=f"{TITLES[r.decision]} — {r.candidate.title}",
            summary=r.candidate.summary,
            reason_shown=r.candidate.reason or "Selected during pre-procedure record review.",
            evidence_ids=r.candidate.evidence_ids,
        ))
    trace.add("composer", "cards", f"Prepared {len(cards)} evidence-backed card(s)")
    return cards
