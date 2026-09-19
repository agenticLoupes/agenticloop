"""Case briefing chat — available for every patient/run, record-grounded, no advice."""
import json

import pytest
from fastapi.testclient import TestClient

from app.case_chat import CaseChatNotFound, EmptyQuestion, answer_case_question, patient_briefing
from app.db import get_conn
from app.main import app


def test_briefing_available_for_every_patient():
    with get_conn() as c:
        ids = [r["id"] for r in c.execute("select id from patient").fetchall()]
    assert len(ids) >= 12
    for pid in ids:
        b = patient_briefing(pid)
        assert b["patient"] is not None
        assert b["patient"]["patient_id"] == pid


def test_briefing_includes_transcript_when_present():
    b = patient_briefing("DEMO-007")
    conv_ids = {r["record_id"] for r in b["conversations"]}
    assert "CONV-007" in conv_ids
    med_ids = {r["record_id"] for r in b["medications"]}
    assert "MED-018" in med_ids


def test_briefing_works_for_patient_without_transcript():
    b = patient_briefing("DEMO-008")
    assert b["patient"]["patient_id"] == "DEMO-008"
    assert b["conversations"] == []


def _insert_run(patient_id: str, procedure: str = "extraction", tooth: int = 30) -> str:
    result = {
        "run_id": "pending",
        "patient_id": patient_id,
        "procedure": procedure,
        "tooth_number": tooth,
        "status": "complete",
        "final_cards": [],
        "skeptic_results": [],
        "dismissed_count": 0,
        "verify_count": 0,
        "summary": f"Guardian investigated records before the planned {procedure}.",
    }
    with get_conn() as c:
        row = c.execute(
            "insert into investigation_run (patient_id, procedure, tooth_number, status, result)"
            " values (%s,%s,%s,'complete',%s) returning id",
            (patient_id, procedure, tooth, json.dumps(result)),
        ).fetchone()
        c.commit()
    return str(row["id"])


def _delete_run(run_id: str) -> None:
    with get_conn() as c:
        c.execute("delete from agent_event where run_id=%s", (run_id,))
        c.execute("delete from investigation_run where id=%s", (run_id,))
        c.commit()


class _FakeLLM:
    def __init__(self, reply: str = "On file: Warfarin (MED-018)."):
        self.reply = reply
        self.messages = None

    def invoke(self, messages):
        self.messages = messages
        return type("R", (), {"content": self.reply})()


def test_ask_grounds_in_this_case_and_blocks_advice(monkeypatch):
    fake = _FakeLLM(
        "Warfarin is listed as active (MED-018). I can explain what the review found, "
        "but clinical decisions and treatment choices remain with you as the dentist."
    )
    monkeypatch.setattr("app.case_chat.get_llm", lambda: fake)
    run_id = _insert_run("DEMO-007")
    try:
        out = answer_case_question(run_id, "Should I extract this tooth?")
        assert "answer" in out
        system = fake.messages[0].content
        assert "NEVER diagnose" in system
        packed = fake.messages[-1].content
        assert "DEMO-007" in packed
        assert "MED-018" in packed
        assert "Should I extract this tooth?" in packed
    finally:
        _delete_run(run_id)


def test_ask_works_for_a_case_without_transcript(monkeypatch):
    fake = _FakeLLM("No visit transcript is on file for this patient.")
    monkeypatch.setattr("app.case_chat.get_llm", lambda: fake)
    run_id = _insert_run("DEMO-008", tooth=3)
    try:
        out = answer_case_question(run_id, "Any visit conversation I should know about?")
        assert out["answer"]
        packed = fake.messages[-1].content
        assert "DEMO-008" in packed
    finally:
        _delete_run(run_id)


def test_ask_rewrites_treatment_advice(monkeypatch):
    fake = _FakeLLM("You should extract this tooth after stopping Warfarin.")
    monkeypatch.setattr("app.case_chat.get_llm", lambda: fake)
    run_id = _insert_run("DEMO-007")
    try:
        out = answer_case_question(run_id, "What should I do?")
        assert "you should" not in out["answer"].lower()
        assert "clinical decisions" in out["answer"].lower()
    finally:
        _delete_run(run_id)


def test_ask_empty_question_raises():
    with pytest.raises(EmptyQuestion):
        answer_case_question("00000000-0000-0000-0000-000000000000", "   ")
    with pytest.raises(CaseChatNotFound):
        answer_case_question("00000000-0000-0000-0000-000000000000", "What was found?")


def test_ask_http_endpoint_for_any_completed_run(monkeypatch):
    fake = _FakeLLM("Cetirizine is also listed as active.")
    monkeypatch.setattr("app.case_chat.get_llm", lambda: fake)
    run_id = _insert_run("DEMO-007")
    try:
        client = TestClient(app)
        res = client.post(
            f"/investigations/{run_id}/ask",
            json={"question": "What medications are on file?", "history": []},
        )
        assert res.status_code == 200
        assert "answer" in res.json()
    finally:
        _delete_run(run_id)
