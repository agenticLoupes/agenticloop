"""Clinical Advisor — the *asked* surface of the product.

The Guardian investigates on its own before a procedure. The Advisor answers a question the
dentist actually typed ("what approaches should I consider for…"), grounding it in this
patient's own records plus published evidence (PubMed / guidelines).

Same contract as the rest of the system: a claim without a source does not ship. After the
model answers, `_enforce_evidence` deterministically drops every record id that does not
resolve to this patient and every citation the tools did not return this turn — the model
cannot cite its way past the retrieval layer.
"""
import json
import re
from pathlib import Path

from langchain_core.messages import ToolMessage
from langgraph.prebuilt import create_react_agent

from app.models import AdvisorAnswer, Approach, Citation, PatientContextItem
from app.provider import get_advisor_llm
from app.tools.records import get_record
from app.tools.registry import build_advisor_tools
from app.trace import Trace

SKILL_PATH = Path(__file__).with_name("advisor_skill.md")

CONTEXT_TEMPLATE = """## This turn

Patient in scope: {patient}
Planned procedure: {procedure}
Tooth: {tooth}

The dentist asks:
{question}

Work the four steps, then return ONLY the JSON object."""

RETRY_NUDGE = ("Your last reply was not the required JSON object. Return ONLY that object, "
               "starting with {{ and ending with }}, using the sources you already retrieved. "
               "Add nothing before or after it.")

# record id prefixes the evidence layer can resolve (mirrors the Skeptic's map)
_TYPE_BY_PREFIX = {"MED": "medication", "ALG": "allergy", "COND": "medical_condition",
                   "DENT": "dental_event", "NOTE": "clinical_note", "IMG": "imaging",
                   "CONV": "conversation", "DEMO": "patient"}


def load_skill() -> str:
    """The advisor's instructions, authored as a skill document (frontmatter stripped)."""
    text = SKILL_PATH.read_text(encoding="utf-8")
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            text = text[end + 4:]
    return text.strip()


def ask(question: str, patient_id: str | None = None, procedure: str | None = None,
        tooth_number: int | None = None, history: list[dict] | None = None,
        trace: Trace | None = None, max_steps: int = 10) -> AdvisorAnswer:
    """Answer one dentist-asked clinical question. Never raises: failures land in .error."""
    trace = trace or Trace("advisor", persist=False)
    answer = AdvisorAnswer(question=question, patient_id=patient_id, procedure=procedure,
                           tooth_number=tooth_number)

    trace.add("advisor", "question", f"Dentist asked: {question}")
    tools = build_advisor_tools(patient_id, procedure, tooth_number, trace)
    if not patient_id:
        trace.add("advisor", "scope", "No patient in scope — answering from published evidence only")

    messages: list = [("system", load_skill())]
    for turn in history or []:
        role = "assistant" if turn.get("role") in ("assistant", "ai") else "user"
        content = (turn.get("content") or "").strip()
        if content:
            messages.append((role, content))
    messages.append(("user", CONTEXT_TEMPLATE.format(
        patient=patient_id or "none (general question)",
        procedure=procedure or "not stated",
        tooth=f"#{tooth_number}" if tooth_number is not None else "not stated",
        question=question,
    )))

    try:
        agent = create_react_agent(get_advisor_llm(), tools)
        result = agent.invoke({"messages": messages},
                              config={"recursion_limit": max_steps * 2 + 5})
        raw = _text_of(result["messages"][-1].content)
        parsed = _parse_json(raw)

        if parsed is None:  # validate/retry once, then fail safely (§22)
            trace.add("advisor", "reformat", "Answer was not valid JSON; asked once more")
            result = agent.invoke(
                {"messages": result["messages"] + [("user", RETRY_NUDGE)]},
                config={"recursion_limit": max_steps + 5})
            raw = _text_of(result["messages"][-1].content)
            parsed = _parse_json(raw)

        retrieved = _citations_seen(result["messages"])
        if parsed is None:
            # No structure, but the prose was still produced from real tool results — keep
            # it as notes rather than discard the turn or invent a shape for it.
            answer.notes = raw.strip()
            trace.add("advisor", "degraded", "Returned unstructured answer; no claim was invented")
        else:
            _fill(answer, parsed, patient_id, retrieved, trace)
    except Exception as e:  # provider/tooling failure -> recoverable demo error (§22)
        answer.status = "error"
        answer.error = f"provider_error: {e}"
        trace.add("advisor", "error", "Advisor failed safely; no unsupported answer shown")

    answer.trace = list(trace.events)
    return answer


def _fill(answer: AdvisorAnswer, parsed: dict, patient_id: str | None,
          retrieved: set[str], trace: Trace) -> None:
    answer.question_focus = str(parsed.get("question_focus") or "")
    answer.patient_communication = str(parsed.get("patient_communication") or "")
    answer.urgent_referral = bool(parsed.get("urgent_referral"))
    answer.cautions = [str(c) for c in _as_list(parsed.get("cautions"))]
    answer.unavailable_sources = [str(s) for s in _as_list(parsed.get("unavailable_sources"))]

    answer.patient_context = _valid_context(_as_list(parsed.get("patient_context")), patient_id)
    answer.approaches, demoted = _valid_approaches(_as_list(parsed.get("approaches")), retrieved)
    answer.cautions.extend(demoted)
    answer.citations = _valid_citations(_as_list(parsed.get("citations")), retrieved)

    if demoted:
        trace.add("advisor", "evidence_check",
                  f"{len(demoted)} approach(es) had no retrieved citation — moved to open questions")
    trace.add("advisor", "answer",
              f"Answered with {len(answer.approaches)} evidence-backed approach(es), "
              f"{len(answer.citations)} citation(s)")


def _valid_context(items: list, patient_id: str | None) -> list[PatientContextItem]:
    """Keep only record ids that resolve to a real record of THIS patient (§12)."""
    out: list[PatientContextItem] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        finding = str(item.get("finding") or "").strip()
        if not finding:
            continue
        ids = [str(i) for i in _as_list(item.get("evidence_ids")) if str(i).strip()]
        good = [i for i in ids if _resolves(i, patient_id)]
        if ids and not good:
            continue  # claimed a source that does not exist -> drop the claim, not just the id
        out.append(PatientContextItem(finding=finding, evidence_ids=good))
    return out


def _resolves(evidence_id: str, patient_id: str | None) -> bool:
    if not patient_id:
        return False
    rtype = _TYPE_BY_PREFIX.get(evidence_id.split("-")[0].upper())
    if not rtype:
        return False
    try:
        rec = get_record(rtype, evidence_id)
    except Exception:
        return False
    return rec is not None and rec.patient_id == patient_id


def _valid_approaches(items: list, retrieved: set[str]) -> tuple[list[Approach], list[str]]:
    """An approach keeps only citations the tools actually returned. None left -> it is an
    open question, not a grounded approach (the skill's own rule, enforced in code)."""
    kept: list[Approach] = []
    demoted: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        name = str(item.get("approach") or "").strip()
        if not name:
            continue
        cites = [c for c in (str(x).strip() for x in _as_list(item.get("citations")))
                 if _cited(c, retrieved)]
        if not cites:
            demoted.append(f"{name} — mentioned without a retrieved source; not presented as "
                           "evidence-backed.")
            continue
        kept.append(Approach(
            approach=name,
            rationale=str(item.get("rationale") or ""),
            patient_specific_considerations=[
                str(c) for c in _as_list(item.get("patient_specific_considerations"))],
            citations=cites,
        ))
    return kept, demoted


def _cited(citation_id: str, retrieved: set[str]) -> bool:
    if not citation_id:
        return False
    if citation_id in retrieved:
        return True
    # tolerate trailing slashes / anchors on guideline URLs
    trimmed = citation_id.rstrip("/").split("#")[0]
    return any(trimmed == r.rstrip("/").split("#")[0] for r in retrieved)


def _valid_citations(items: list, retrieved: set[str]) -> list[Citation]:
    out, seen = [], set()
    for item in items:
        cid = str(item.get("citation_id") or "").strip() if isinstance(item, dict) else str(item).strip()
        if not _cited(cid, retrieved) or cid in seen:
            continue
        seen.add(cid)
        label = str(item.get("label") or "") if isinstance(item, dict) else ""
        url = item.get("url") if isinstance(item, dict) else None
        if not url:
            url = cid if cid.startswith("http") else (
                f"https://pubmed.ncbi.nlm.nih.gov/{cid.split(':', 1)[1]}/"
                if cid.upper().startswith("PMID:") else None)
        out.append(Citation(citation_id=cid, label=label, url=url))
    return out


def _citations_seen(messages: list) -> set[str]:
    """Every PMID and URL the search tools actually returned this turn."""
    found: set[str] = set()
    for m in messages:
        if not isinstance(m, ToolMessage):
            continue
        text = _text_of(m.content)
        found.update(re.findall(r"PMID:\d+", text))
        found.update(re.findall(r"https?://[^\s\"'\\)<>]+", text))
    return found


def _text_of(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):  # Gemini returns a list of content parts
        return "\n".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in content)
    return json.dumps(content, default=str)


def _parse_json(text: str) -> dict | None:
    """Tolerate fenced/annotated JSON; None when there is no object to read."""
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        parsed = json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _as_list(value) -> list:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]
