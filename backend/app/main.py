"""DentAssist Guardian API (§16). Model keys live server-side only (§14)."""
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.db import get_conn
from app.graph import run_investigation
from app.tools.records import TYPE_CONFIG, get_record

app = FastAPI(title="DentAssist Guardian", description="SYNTHETIC DATA — PROTOTYPE")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

ASSETS = Path(__file__).resolve().parents[2] / "db" / "assets"
app.mount("/assets", StaticFiles(directory=ASSETS), name="assets")


class InvestigationRequest(BaseModel):
    patient_id: str
    procedure: str
    tooth_number: int | None = None


@app.get("/health")
def health():
    return {"ok": True, "banner": "SYNTHETIC DATA — PROTOTYPE"}


@app.get("/demo/patients")
def demo_patients():
    with get_conn() as c:
        rows = c.execute("select id, demo_identifier, display_name from patient order by id").fetchall()
    return rows


@app.get("/patients/{patient_id}")
def patient(patient_id: str):
    r = get_record("patient", patient_id)
    if not r:
        raise HTTPException(404, "patient not found")
    return r.model_dump(mode="json")


@app.post("/investigations")
def create_investigation(req: InvestigationRequest):
    state = run_investigation(req.patient_id, req.procedure, req.tooth_number)
    if state.status == "error" and not state.run_id:
        raise HTTPException(400, state.error)
    return state.model_dump(mode="json")


@app.get("/investigations/{run_id}")
def get_investigation(run_id: str):
    with get_conn() as c:
        row = c.execute("select * from investigation_run where id=%s", (run_id,)).fetchone()
    if not row:
        raise HTTPException(404, "run not found")
    return {k: v for k, v in row.items()}


@app.get("/investigations/{run_id}/trace")
def get_trace(run_id: str):
    with get_conn() as c:
        rows = c.execute(
            "select sequence_no, agent, event_type, summary from agent_event"
            " where run_id=%s order by sequence_no", (run_id,)).fetchall()
    return rows


@app.get("/evidence/{record_type}/{record_id}")
def evidence(record_type: str, record_id: str):
    if record_type not in TYPE_CONFIG:
        raise HTTPException(404, "unknown record type")
    r = get_record(record_type, record_id)
    if not r:
        raise HTTPException(404, "record not found")
    return r.model_dump(mode="json")


@app.post("/demo/reset")
def demo_reset():
    with get_conn() as c:
        c.execute("truncate table agent_event, investigation_run")
        c.commit()
    return {"ok": True}
