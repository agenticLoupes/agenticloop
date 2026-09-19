"""Guardian Investigator (§9.2) — model-driven tool selection; emits candidates.

Uses a LangGraph ReAct agent (do not build an agent runtime, §14). The playbook is a
starting HINT only — the model chooses and follows discoveries (§10 agency).
"""
import json

from langgraph.prebuilt import create_react_agent

from app.models import Candidate
from app.playbook import hint_tools_for
from app.provider import get_llm
from app.tools.registry import build_tools
from app.trace import Trace

SYSTEM = """You are Guardian, a pre-procedure record investigator for a dentist.
The dentist is about to perform: {procedure}{tooth}. Patient: {patient_id} (synthetic data).

Your mission: investigate this patient's OWN records for information that may deserve the
dentist's review BEFORE beginning. You decide which record sources to inspect, in what order,
and when to stop. Follow discoveries — if a record hints at something (e.g. a note mentions a
medication change), inspect the related source (e.g. medication history, visit transcripts).
Always check prior clinical notes and visit transcripts with a broad query (e.g. 'medication')
before concluding nothing is relevant — easy-to-miss context often lives there. A record whose
current status cannot be established from the sources is still a candidate (say so in its
summary); uncertainty is for the verifier to decide, not a reason to omit.
If an imaging record covers the procedure site, inspect it with read_imaging to confirm its
region and relevance. When read_imaging reports the image is relevant to the procedure site,
INCLUDE that imaging record as a candidate (title it as an imaging record to review, evidence id
IMG-…) — the dentist reviews the image itself; you never interpret it.
Commonly relevant sources for this procedure (a hint, not an order): {hints}.

STRICT RULES:
- You are NOT diagnosing, NOT recommending treatment, NOT prescribing. Never do so.
- Every factual claim must come from a tool result and carry its record_id.
- Do not call every tool blindly; choose based on the procedure and what you find. Stop when
  you have enough.
- PROPOSE LIBERALLY: you investigate broadly; a separate verifier challenges aggressively and
  decides what actually deserves attention. Any ACTIVE medication, DOCUMENTED allergy, ACTIVE
  condition, contradiction between sources, uncertain status, or site-relevant imaging with
  plausible relevance to this procedure should be proposed as a candidate — do not pre-filter
  to only the strongest findings. Silence is correct ONLY when the record genuinely holds
  nothing plausibly relevant.

When done, output ONLY a JSON array of candidate records worth the dentist's review
(empty array if none):
[{{"title": "...", "summary": "...", "record_type": "...", "evidence_ids": ["MED-018"],
   "reason": "why this record was selected (pattern/context), never advice"}}]
"""


def investigate(context: dict, trace: Trace, max_steps: int = 12) -> list[Candidate]:
    patient_id = context["patient_id"]
    procedure = context["procedure"]
    tooth = context.get("tooth_number")
    imaging_findings: list[dict] = []
    tools = build_tools(patient_id, procedure, tooth, trace, imaging_findings)
    agent = create_react_agent(get_llm(), tools)

    prompt = SYSTEM.format(
        procedure=procedure,
        tooth=f" on tooth #{tooth}" if tooth is not None else "",
        patient_id=patient_id,
        hints=", ".join(hint_tools_for(procedure)) or "none listed",
    )
    result = agent.invoke(
        {"messages": [("system", prompt), ("user", "Begin the pre-procedure investigation.")]},
        config={"recursion_limit": max_steps * 2 + 5},
    )
    text = result["messages"][-1].content
    if not isinstance(text, str):
        text = json.dumps(text) if not isinstance(text, list) else " ".join(
            p.get("text", "") if isinstance(p, dict) else str(p) for p in text)

    candidates = _parse_candidates(text)

    # Deterministic backstop: imaging the vision gate validated as relevant to the procedure
    # site enters the candidate pool even if the model under-reports it. The Skeptic still
    # challenges it like any candidate. (ponytail: plumbing, not judgment — Jev judges.)
    covered = {eid for c in candidates for eid in c.evidence_ids}
    for f in imaging_findings:
        eid = f.get("evidence_id")
        if eid and f.get("relevant") and f.get("region_match") and eid not in covered:
            candidates.append(Candidate(
                title="Imaging record covering the procedure site",
                summary=f"An imaging record ({eid}) covers the {f.get('region_label', 'procedure')} region.",
                record_type="imaging",
                evidence_ids=[eid],
                reason="Recent imaging of the procedure site was located during pre-procedure review.",
            ))
            covered.add(eid)

    trace.add("guardian", "candidates",
              f"Proposed {len(candidates)} candidate record(s) for challenge")
    return candidates


def _parse_candidates(text: str) -> list[Candidate]:
    # tolerate fenced/annotated JSON; fail safe to [] (silence is valid, §22)
    start, end = text.find("["), text.rfind("]")
    if start == -1 or end <= start:
        return []
    try:
        raw = json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return []
    out = []
    for item in raw:
        try:
            c = Candidate(**item)
            if c.evidence_ids:  # NO EVIDENCE ID -> NO CANDIDATE (§12)
                out.append(c)
        except Exception:
            continue
    return out
