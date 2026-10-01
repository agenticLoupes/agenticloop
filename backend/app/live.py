"""Live voice support for the phone (/live route in the UI).

The phone talks to the Gemini Live API directly over its own WebSocket; this backend
never relays audio. It only:
  - mints short-lived ephemeral tokens, so GOOGLE_API_KEY never reaches the browser;
  - tells the laptop which investigation the phone just started (latest-run);
  - mirrors the spoken conversation so the laptop can show it (transcript).

The Guardian pipeline itself is unchanged: the phone starts runs via POST /investigations.
"""
import datetime as dt
import threading
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import get_settings
from app.db import get_conn

router = APIRouter(prefix="/live", tags=["live"])

# The SDK only accepts ephemeral tokens on v1alpha (google/genai/live.py enforces it).
# The browser must connect with the same version, so we hand it back with the token.
LIVE_API_VERSION = "v1alpha"


@router.post("/token")
def live_token():
    """One-use token for a single Live session. Reconnects fetch a fresh one.

    Deliberately not locked to a config: a constrained token ignores the client's
    LiveConnectConfig, which would silently drop the tools and system instruction.
    """
    s = get_settings()
    if not s.google_api_key:
        raise HTTPException(503, "GOOGLE_API_KEY is not set on the backend")
    from google import genai  # imported lazily: only this route needs it

    client = genai.Client(api_key=s.google_api_key,
                          http_options={"api_version": LIVE_API_VERSION})
    now = dt.datetime.now(tz=dt.timezone.utc)
    try:
        token = client.auth_tokens.create(config={
            "uses": 1,
            "expire_time": now + dt.timedelta(minutes=30),
            "new_session_expire_time": now + dt.timedelta(minutes=2),
            "http_options": {"api_version": LIVE_API_VERSION},
        })
    except Exception as e:  # surface the provider message; the phone shows a retry
        raise HTTPException(502, f"token_error: {e}") from e
    return {"token": token.name, "model": s.gemini_live_model, "api_version": LIVE_API_VERSION}


@router.get("/latest-run")
def latest_run():
    """Most recent investigation, so the laptop can follow runs the phone starts."""
    with get_conn() as c:
        row = c.execute(
            "select id, patient_id, procedure, tooth_number, status, started_at"
            " from investigation_run order by started_at desc limit 1").fetchone()
    return row


# ---- transcript mirror (in memory; the demo runs one backend process) ------------
class TranscriptLine(BaseModel):
    role: Literal["dentist", "assistant", "system"]
    text: str


_lines: list[dict] = []
_next_id = 1
_lock = threading.Lock()
_MAX_LINES = 500


@router.post("/transcript")
def add_transcript_line(line: TranscriptLine):
    global _next_id
    text = line.text.strip()
    if not text:
        return {"id": None}
    with _lock:
        entry = {"id": _next_id, "role": line.role, "text": text,
                 "at": dt.datetime.now(tz=dt.timezone.utc).isoformat()}
        _next_id += 1
        _lines.append(entry)
        del _lines[:-_MAX_LINES]
    return {"id": entry["id"]}


@router.get("/transcript")
def get_transcript(since: int = 0):
    """Lines with id > since, oldest first. Ids only ever grow, so polling is safe."""
    with _lock:
        return [l for l in _lines if l["id"] > since]
