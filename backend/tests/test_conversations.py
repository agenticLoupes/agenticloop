from app.tools import conversations
from app.models import Record


def test_search_conversations_finds_blood_thinner_transcript():
    rs = conversations.search_conversations("DEMO-007", "blood thinner")
    hit = next(r for r in rs if r.record_id == "CONV-007")
    assert isinstance(hit, Record)
    assert hit.patient_id == "DEMO-007"
    assert hit.data["transcript_text"]


def test_search_conversations_no_match_returns_empty():
    assert conversations.search_conversations("DEMO-007", "zzz-no-such-text-zzz") == []
