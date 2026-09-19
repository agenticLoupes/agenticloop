"""Clinical Advisor — evidence contract and wiring.

Hermetic: no database, no network, no model call. The pieces that touch those are
monkeypatched, so these run anywhere (the live path is exercised by scripts/ask_advisor.py).
"""
import json

import pytest
from langchain_core.messages import AIMessage, ToolMessage

from app.agents import advisor
from app.models import Record
from app.tools import literature, records
from app.tools.registry import build_advisor_tools
from app.trace import Trace


def _trace() -> Trace:
    return Trace("test", persist=False)


# --- the skill document is the prompt -------------------------------------------------

def test_skill_loads_without_frontmatter():
    skill = advisor.load_skill()
    assert not skill.startswith("---")
    assert "Clinical Advisor" in skill
    # the workflow steps the agent is expected to follow
    for step in ("Read the question", "Retrieve this patient's context",
                 "Ground the approaches", "Compose"):
        assert step in skill
    assert '"approaches"' in skill  # output schema is part of the prompt


# --- toolset wiring -------------------------------------------------------------------

def test_advisor_tools_include_records_and_literature():
    names = {t.name for t in build_advisor_tools("DEMO-007", "extraction", 30, _trace())}
    assert {"get_active_medications", "get_allergies", "search_conversations"} <= names
    assert {"search_pubmed", "search_clinical_guidelines"} <= names


def test_advisor_never_interprets_images():
    names = {t.name for t in build_advisor_tools("DEMO-007", "extraction", 30, _trace())}
    assert "read_imaging" not in names  # locating imaging is the Guardian's gated job
    assert "get_imaging" in names       # listing that imaging exists is fine


def test_advisor_without_patient_gets_literature_only():
    names = {t.name for t in build_advisor_tools(None, None, None, _trace())}
    assert names == {"search_pubmed", "search_clinical_guidelines"}


def test_record_tools_trace_under_the_advisor_not_the_guardian(monkeypatch):
    """Advisor activity must be attributable to the Advisor in the trace (§20)."""
    monkeypatch.setattr(records, "get_active_medications", lambda pid: [])
    trace = _trace()
    tools = {t.name: t for t in build_advisor_tools("DEMO-007", "extraction", 30, trace)}
    tools["get_active_medications"].invoke({})
    assert [(e["agent"], e["event_type"]) for e in trace.events] == [("advisor", "tool_call")]


# --- parsing --------------------------------------------------------------------------

def test_parse_json_tolerates_fencing_and_prose():
    assert advisor._parse_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert advisor._parse_json('Here you go: {"a": 1} — hope that helps') == {"a": 1}
    assert advisor._parse_json("no object here") is None
    assert advisor._parse_json('[1, 2]') is None  # an array is not the required object


def test_citations_seen_reads_only_tool_output():
    messages = [
        AIMessage(content="I will cite PMID:99999999"),  # model prose is NOT a source
        ToolMessage(content=json.dumps({"results": [
            {"citation_id": "PMID:12345678",
             "url": "https://pubmed.ncbi.nlm.nih.gov/12345678/"},
            {"citation_id": "https://www.sdcep.org.uk/published-guidance/"},
        ]}), tool_call_id="1"),
    ]
    seen = advisor._citations_seen(messages)
    assert "PMID:12345678" in seen
    assert "https://www.sdcep.org.uk/published-guidance/" in seen
    assert "PMID:99999999" not in seen


# --- the evidence contract ------------------------------------------------------------

def test_approach_without_retrieved_citation_is_demoted():
    kept, demoted = advisor._valid_approaches(
        [{"approach": "Grounded option", "citations": ["PMID:12345678"]},
         {"approach": "Invented option", "citations": ["PMID:00000000"]},
         {"approach": "Uncited option", "citations": []}],
        retrieved={"PMID:12345678"})
    assert [a.approach for a in kept] == ["Grounded option"]
    assert len(demoted) == 2
    assert all("not presented as evidence-backed" in d for d in demoted)


def test_citation_matching_tolerates_trailing_slash_and_anchor():
    assert advisor._cited("https://sdcep.org.uk/guide", {"https://sdcep.org.uk/guide/"})
    assert advisor._cited("https://sdcep.org.uk/guide#sec2", {"https://sdcep.org.uk/guide"})
    assert not advisor._cited("https://example.com/other", {"https://sdcep.org.uk/guide"})
    assert not advisor._cited("", {"PMID:1"})


def test_citations_are_filtered_deduped_and_linked():
    cites = advisor._valid_citations(
        [{"citation_id": "PMID:12345678", "label": "Review"},
         {"citation_id": "PMID:12345678", "label": "duplicate"},
         {"citation_id": "PMID:87654321", "label": "never retrieved"}],
        retrieved={"PMID:12345678"})
    assert len(cites) == 1
    assert cites[0].url == "https://pubmed.ncbi.nlm.nih.gov/12345678/"


def test_patient_context_drops_unresolvable_records(monkeypatch):
    def fake_get_record(rtype, rid):
        if rid == "MED-018":
            return Record(record_id=rid, record_type=rtype, patient_id="DEMO-007")
        if rid == "MED-999":
            return Record(record_id=rid, record_type=rtype, patient_id="DEMO-008")  # other patient
        return None

    monkeypatch.setattr(advisor, "get_record", fake_get_record)
    items = advisor._valid_context([
        {"finding": "Active warfarin", "evidence_ids": ["MED-018"]},
        {"finding": "Belongs to someone else", "evidence_ids": ["MED-999"]},
        {"finding": "Cites a record that does not exist", "evidence_ids": ["MED-404"]},
        {"finding": "No source at all", "evidence_ids": []},
    ], patient_id="DEMO-007")
    findings = [i.finding for i in items]
    assert findings == ["Active warfarin", "No source at all"]  # unsourced claim keeps no id
    assert items[0].evidence_ids == ["MED-018"]


def test_no_patient_means_no_patient_record_is_ever_cited():
    items = advisor._valid_context(
        [{"finding": "invented patient fact", "evidence_ids": ["MED-018"]}], patient_id=None)
    assert items == []


# --- end-to-end through a stubbed model -----------------------------------------------

class _StubAgent:
    """Stands in for the ReAct agent: returns canned tool output + a final JSON answer."""

    def __init__(self, final: str, tool_payload: dict | None = None):
        self.final = final
        self.tool_payload = tool_payload or {}
        self.calls = 0

    def invoke(self, state, config=None):
        self.calls += 1
        return {"messages": [
            ToolMessage(content=json.dumps(self.tool_payload), tool_call_id="1"),
            AIMessage(content=self.final),
        ]}


def _stub(monkeypatch, agent):
    monkeypatch.setattr(advisor, "create_react_agent", lambda *a, **k: agent)
    monkeypatch.setattr(advisor, "get_advisor_llm", lambda: object())
    monkeypatch.setattr(advisor, "build_advisor_tools", lambda *a, **k: [])


def test_ask_returns_structured_grounded_answer(monkeypatch):
    payload = {"results": [{"citation_id": "PMID:12345678",
                            "url": "https://pubmed.ncbi.nlm.nih.gov/12345678/"}]}
    final = json.dumps({
        "question_focus": "Extraction under anticoagulation",
        "patient_context": [],
        "approaches": [{"approach": "Local haemostatic measures",
                        "rationale": "Guideline-supported",
                        "patient_specific_considerations": ["active anticoagulant"],
                        "citations": ["PMID:12345678"]}],
        "cautions": ["Confirm INR timing"],
        "patient_communication": "We can usually do this safely without stopping your medicine.",
        "urgent_referral": False,
        "citations": [{"citation_id": "PMID:12345678", "label": "Systematic review"}],
        "unavailable_sources": [],
    })
    _stub(monkeypatch, _StubAgent(final, payload))

    ans = advisor.ask("What approaches for extraction on a warfarin patient?",
                      procedure="extraction", tooth_number=30)
    assert ans.status == "complete"
    assert ans.question_focus == "Extraction under anticoagulation"
    assert [a.approach for a in ans.approaches] == ["Local haemostatic measures"]
    assert ans.citations[0].citation_id == "PMID:12345678"
    assert "Confirm INR timing" in ans.cautions
    assert any(e["event_type"] == "answer" for e in ans.trace)


def test_ask_retries_once_then_keeps_prose_without_inventing(monkeypatch):
    agent = _StubAgent("I could not produce JSON.", {"results": []})
    _stub(monkeypatch, agent)

    ans = advisor.ask("anything")
    assert agent.calls == 2  # validate/retry once (§22)
    assert ans.status == "complete"
    assert ans.approaches == [] and ans.citations == []
    assert ans.notes == "I could not produce JSON."
    assert any(e["event_type"] == "degraded" for e in ans.trace)


def test_ask_fails_safely_on_provider_error(monkeypatch):
    class Boom:
        def invoke(self, *a, **k):
            raise RuntimeError("gemini down")

    _stub(monkeypatch, Boom())
    ans = advisor.ask("anything")
    assert ans.status == "error"
    assert "provider_error" in ans.error
    assert ans.approaches == []  # nothing invented on failure


def test_ask_never_leaks_another_patients_records(monkeypatch):
    final = json.dumps({"patient_context": [
        {"finding": "someone else's medication", "evidence_ids": ["MED-999"]}]})
    _stub(monkeypatch, _StubAgent(final, {}))
    monkeypatch.setattr(advisor, "get_record", lambda t, i: Record(
        record_id=i, record_type=t, patient_id="DEMO-008"))

    ans = advisor.ask("q", patient_id="DEMO-007")
    assert ans.patient_context == []


# --- external sources degrade, never invent -------------------------------------------

def test_pubmed_unavailable_is_reported_not_invented(monkeypatch):
    class BoomClient:
        def __init__(self, *a, **k): pass
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def get(self, *a, **k): raise OSError("network down")

    monkeypatch.setattr(literature.httpx, "Client", BoomClient)
    out = literature.search_pubmed("pericoronitis")
    assert out["available"] is False and out["results"] == []
    assert "unavailable" in out["reason"]


def test_guidelines_unavailable_when_ddgs_missing(monkeypatch):
    import builtins
    real_import = builtins.__import__

    def no_ddgs(name, *a, **k):
        if name == "ddgs":
            raise ImportError("no ddgs")
        return real_import(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", no_ddgs)
    out = literature.search_clinical_guidelines("pericoronitis", "sdcep")
    assert out["available"] is False and out["results"] == []


def test_guideline_site_filter_scopes_the_search(monkeypatch):
    captured = {}

    class FakeDDGS:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def text(self, term, max_results=4):
            captured["term"] = term
            return [{"title": "SDCEP guidance", "href": "https://www.sdcep.org.uk/x",
                     "body": "snippet"}]

    import ddgs
    monkeypatch.setattr(ddgs, "DDGS", FakeDDGS)
    out = literature.search_clinical_guidelines("pericoronitis", "sdcep")
    assert "site:sdcep.org.uk" in captured["term"]
    assert out["results"][0]["citation_id"] == "https://www.sdcep.org.uk/x"


def test_pubmed_broadens_when_high_evidence_filter_finds_nothing(monkeypatch):
    calls = []

    class FakeClient:
        def __init__(self, *a, **k): pass
        def __enter__(self): return self
        def __exit__(self, *a): return False

        def get(self, url, params=None):
            calls.append(params.get("term", url))
            return _FakeResp(url, params)

    class _FakeResp:
        def __init__(self, url, params):
            self.url, self.params = url, params

        def raise_for_status(self): pass

        def json(self):
            if "esearch" in self.url:
                filtered = "[Filter]" in self.params["term"]
                return {"esearchresult": {"idlist": [] if filtered else ["12345678"]}}
            return {"result": {"12345678": {"title": "A trial", "source": "J Dent",
                                            "pubdate": "2024", "pubtype": ["Journal Article"]}}}

    monkeypatch.setattr(literature.httpx, "Client", FakeClient)
    out = literature.search_pubmed("very specific question")
    assert out["available"] and out["results"][0]["citation_id"] == "PMID:12345678"
    assert "weaker evidence" in out["note"]
    assert len([c for c in calls if "[Filter]" in str(c)]) == 1  # filtered first, then broadened


# --- trace ----------------------------------------------------------------------------

def test_advisor_trace_is_memory_only():
    """The advisor has no investigation_run row, so its trace must not try to persist."""
    t = Trace("advisor", persist=False)
    t.add("advisor", "tool_call", "Searched PubMed")  # would raise if it hit the DB
    assert t.events[0]["summary"] == "Searched PubMed"


@pytest.mark.parametrize("value,expected", [(None, []), ("x", ["x"]), (["a", "b"], ["a", "b"])])
def test_as_list_normalizes_model_sloppiness(value, expected):
    assert advisor._as_list(value) == expected


# --- HTTP surface ---------------------------------------------------------------------

def _client(monkeypatch):
    from fastapi.testclient import TestClient

    from app import main

    monkeypatch.setattr(main, "get_record", lambda t, i: (
        Record(record_id=i, record_type=t, patient_id=i) if i == "DEMO-007" else None))
    return TestClient(main.app), main


def _capture_ask(monkeypatch, main) -> dict:
    from app.models import AdvisorAnswer

    captured: dict = {}

    def fake_ask(**kwargs):
        captured.update(kwargs)
        return AdvisorAnswer(question=kwargs["question"], question_focus="focused")

    monkeypatch.setattr(main.advisor, "ask", fake_ask)
    return captured


def test_ask_endpoint_returns_the_answer(monkeypatch):
    client, main = _client(monkeypatch)
    captured = _capture_ask(monkeypatch, main)
    r = client.post("/advisor/ask", json={
        "question": "  What approaches for this extraction?  ",
        "patient_id": "DEMO-007", "procedure": "extraction", "tooth_number": 30})
    assert r.status_code == 200
    assert r.json()["question_focus"] == "focused"
    assert captured["question"] == "What approaches for this extraction?"  # trimmed
    assert captured["patient_id"] == "DEMO-007"


def test_ask_endpoint_rejects_unusable_questions(monkeypatch):
    client, _ = _client(monkeypatch)
    assert client.post("/advisor/ask", json={"question": "   "}).status_code == 400
    assert client.post("/advisor/ask", json={"question": "x" * 2001}).status_code == 400


def test_ask_endpoint_rejects_unknown_patient(monkeypatch):
    client, _ = _client(monkeypatch)
    r = client.post("/advisor/ask", json={"question": "q", "patient_id": "DEMO-404"})
    assert r.status_code == 404


def test_ask_endpoint_bounds_conversation_history(monkeypatch):
    client, main = _client(monkeypatch)
    captured = _capture_ask(monkeypatch, main)
    history = [{"role": "user", "content": f"turn {i}"} for i in range(30)]
    client.post("/advisor/ask", json={"question": "q", "history": history})
    assert len(captured["history"]) == 10  # prompt stays bounded
    assert captured["history"][-1]["content"] == "turn 29"
