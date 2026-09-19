"""Drive the Clinical Advisor from the terminal (no server, no UI).

Usage:
  .venv/bin/python scripts/ask_advisor.py "what approaches for localized acute pericoronitis?"
  .venv/bin/python scripts/ask_advisor.py "options here?" --patient DEMO-007 --procedure extraction --tooth 30

Runs the same code path as POST /advisor/ask, printing the tool activity as it happens.
Exit code 0 when the advisor answered, 1 on a recoverable provider error.
"""
import argparse
import sys

from app.agents import advisor
from app.trace import Trace

sys.stdout.reconfigure(line_buffering=True)  # show tool activity live in the terminal


class LiveTrace(Trace):
    """In-memory trace that prints each step as the agent takes it."""

    def add(self, agent: str, event_type: str, summary: str, metadata: dict | None = None):
        super().add(agent, event_type, summary, metadata)
        print(f"  [{event_type}] {summary}", flush=True)


def main() -> int:
    p = argparse.ArgumentParser(description="Ask the DentAssist Clinical Advisor")
    p.add_argument("question", help="the clinical question, in quotes")
    p.add_argument("--patient", default=None, help="patient id, e.g. DEMO-007")
    p.add_argument("--procedure", default=None, help="e.g. extraction")
    p.add_argument("--tooth", type=int, default=None)
    args = p.parse_args()

    print(f"\nQuestion: {args.question}")
    print("=" * 70)
    answer = advisor.ask(
        question=args.question,
        patient_id=args.patient,
        procedure=args.procedure,
        tooth_number=args.tooth,
        trace=LiveTrace("cli", persist=False),
    )
    print("=" * 70)

    if answer.status == "error":
        print(f"\nRecoverable error: {answer.error}", file=sys.stderr)
        print("\nChecks: is GOOGLE_API_KEY set in backend/.env (or ADVISOR_PROVIDER=ollama with "
              "ollama serve running)? Is the network up for PubMed?", file=sys.stderr)
        return 1

    if answer.question_focus:
        print(f"\nFocus: {answer.question_focus}")
    for item in answer.patient_context:
        print(f"\n· {item.finding}\n    record: {', '.join(item.evidence_ids) or 'none'}")
    for a in answer.approaches:
        print(f"\n▸ {a.approach}\n    {a.rationale}")
        for c in a.patient_specific_considerations:
            print(f"    - this patient: {c}")
        print(f"    cited: {', '.join(a.citations)}")
    for c in answer.cautions:
        print(f"\n! {c}")
    if answer.patient_communication:
        print(f"\nFor the patient: {answer.patient_communication}")
    if answer.urgent_referral:
        print("\nURGENT: a retrieved source describes this as needing immediate care.")
    if answer.unavailable_sources:
        print(f"\nUnavailable sources: {', '.join(answer.unavailable_sources)}")
    if answer.notes:
        print(f"\nUnstructured answer:\n{answer.notes}")
    print(f"\nCitations ({len(answer.citations)}):")
    for c in answer.citations:
        print(f"  {c.citation_id}  {c.label}  {c.url or ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
