"""/live routes: token minting, latest-run, transcript mirror. No DB or Gemini calls."""
from contextlib import contextmanager
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import app.live as live
from app.config import get_settings
from app.main import app


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def settings(monkeypatch):
    get_settings.cache_clear()
    yield monkeypatch
    get_settings.cache_clear()


def test_token_requires_key(client, settings):
    settings.setenv("GOOGLE_API_KEY", "")
    assert client.post("/live/token").status_code == 503


def test_token_is_single_use_v1alpha_and_unlocked(client, settings):
    settings.setenv("GOOGLE_API_KEY", "k")
    settings.setenv("GEMINI_LIVE_MODEL", "gemini-test-live")
    seen = {}

    class FakeClient:
        def __init__(self, api_key, http_options):
            seen["client"] = (api_key, http_options)
            self.auth_tokens = SimpleNamespace(create=self._create)

        def _create(self, config):
            seen["config"] = config
            return SimpleNamespace(name="auth_tokens/abc")

    import google.genai
    settings.setattr(google.genai, "Client", FakeClient)

    r = client.post("/live/token")
    assert r.status_code == 200
    assert r.json() == {"token": "auth_tokens/abc", "model": "gemini-test-live",
                        "api_version": "v1alpha"}
    assert seen["client"] == ("k", {"api_version": "v1alpha"})
    assert seen["config"]["uses"] == 1
    # a constrained token would override the phone's tools + system instruction
    assert "live_connect_constraints" not in seen["config"]


def test_latest_run(client, monkeypatch):
    row = {"id": "r1", "patient_id": "DEMO-007", "procedure": "extraction",
           "tooth_number": 30, "status": "running", "started_at": "2026-09-19T21:00:00Z"}

    @contextmanager
    def fake_conn():
        yield SimpleNamespace(execute=lambda *a: SimpleNamespace(fetchone=lambda: row))

    monkeypatch.setattr(live, "get_conn", fake_conn)
    assert client.get("/live/latest-run").json() == row


def test_transcript_mirror_polls_by_id(client):
    base = client.get("/live/transcript").json()
    since = base[-1]["id"] if base else 0
    a = client.post("/live/transcript", json={"role": "dentist", "text": " extraction on thirty "})
    b = client.post("/live/transcript", json={"role": "assistant", "text": "Starting the review."})
    assert client.post("/live/transcript", json={"role": "dentist", "text": "  "}).json() == {"id": None}
    assert client.post("/live/transcript", json={"role": "patient", "text": "x"}).status_code == 422

    lines = client.get("/live/transcript", params={"since": since}).json()
    assert [(l["role"], l["text"]) for l in lines] == [
        ("dentist", "extraction on thirty"), ("assistant", "Starting the review.")]
    assert client.get("/live/transcript", params={"since": a.json()["id"]}).json()[0]["id"] == b.json()["id"]
