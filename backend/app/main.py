"""DentAssist Guardian API (§16). Model keys live server-side only (§14)."""
from pathlib import Path

import uuid

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.agents import advisor
from app.case_chat import (
    CaseChatNotFound,
    CaseChatUnavailable,
    EmptyQuestion,
    answer_case_question,
)
from app.db import get_conn
from app.graph import execute_run, start_run
from app.live import router as live_router
from app.tools.records import TYPE_CONFIG, get_record

app = FastAPI(title="DentAssist Guardian", description="SYNTHETIC DATA — PROTOTYPE")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(live_router)

ASSETS = Path(__file__).resolve().parents[2] / "db" / "assets"
app.mount("/assets", StaticFiles(directory=ASSETS), name="assets")


class InvestigationRequest(BaseModel):
    patient_id: str
    procedure: str
    tooth_number: int | None = None


class AdvisorTurn(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class AdvisorRequest(BaseModel):
    """A question the dentist typed. Patient context is optional — without it the Advisor
    answers from published evidence only and cites no patient record."""
    question: str
    patient_id: str | None = None
    procedure: str | None = None
    tooth_number: int | None = None
    history: list[AdvisorTurn] = []


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
def create_investigation(req: InvestigationRequest, background: BackgroundTasks):
    """Returns run_id immediately; the agent runs in the background (§15 polling model).

    The UI polls GET /investigations/{run_id} (status/result) and /trace (live steps).
    """
    run_id, ctx_or_err = start_run(req.patient_id, req.procedure, req.tooth_number)
    if run_id is None:
        raise HTTPException(400, ctx_or_err)
    background.add_task(execute_run, run_id, ctx_or_err)
    return {"run_id": run_id, "status": "running"}


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


@app.post("/advisor/ask")
def advisor_ask(req: AdvisorRequest):
    """Answer a dentist's clinical question from this patient's records + published evidence.

    Synchronous: the retrieval loop is a handful of calls, and the answer is only useful
    whole. FastAPI runs this sync handler in a worker thread, so polling keeps working.
    """
    question = (req.question or "").strip()
    if not question:
        raise HTTPException(400, "question_required")
    if len(question) > 2000:
        raise HTTPException(400, "question too long (2000 chars max)")
    if req.patient_id and get_record("patient", req.patient_id) is None:
        raise HTTPException(404, "patient not found")

    answer = advisor.ask(
        question=question,
        patient_id=req.patient_id,
        procedure=req.procedure,
        tooth_number=req.tooth_number,
        history=[t.model_dump() for t in req.history[-10:]],  # bound the prompt
    )
    return answer.model_dump(mode="json")


@app.get("/evidence/{record_type}/{record_id}")
def evidence(record_type: str, record_id: str):
    if record_type not in TYPE_CONFIG:
        raise HTTPException(404, "unknown record type")
    r = get_record(record_type, record_id)
    if not r:
        raise HTTPException(404, "record not found")
    return r.model_dump(mode="json")


class ChatTurn(BaseModel):
    role: str
    content: str


class AskRequest(BaseModel):
    question: str
    history: list[ChatTurn] = []


@app.post("/investigations/{run_id}/ask")
def ask_about_review(run_id: str, req: AskRequest):
    """Case briefing Q&A for this run — every patient. Explains the record, never advises."""
    try:
        return answer_case_question(
            run_id,
            req.question,
            [t.model_dump() for t in req.history],
        )
    except CaseChatNotFound:
        raise HTTPException(404, "run not found or incomplete")
    except EmptyQuestion:
        raise HTTPException(400, "question required")
    except CaseChatUnavailable:
        raise HTTPException(503, "explainer unavailable — the review itself is unaffected")


@app.post("/uploads/imaging")
async def upload_imaging(
    patient_id: str = Form(...),
    tooth_number: int | None = Form(None),
    file: UploadFile = File(...),
):
    """Attach a sample radiograph to a patient's record for this demo.

    Uploads carry no authored ground-truth label, so read_imaging can only mark them
    uncertain → the Skeptic lands on VERIFY. They can never SURFACE autonomously.
    SAMPLE / SYNTHETIC IMAGES ONLY — never real patient data.
    """
    if get_record("patient", patient_id) is None:
        raise HTTPException(404, "patient not found")
    if file.content_type not in ("image/png", "image/jpeg"):
        raise HTTPException(400, "png or jpeg only")
    data = await file.read()
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(400, "file too large (5MB max)")
    ext = "png" if file.content_type == "image/png" else "jpg"
    rid = f"IMG-UP-{uuid.uuid4().hex[:6].upper()}"
    dest = ASSETS / "uploads"
    dest.mkdir(exist_ok=True)
    (dest / f"{rid}.{ext}").write_bytes(data)
    with get_conn() as c:
        c.execute(
            "insert into imaging_study (id, patient_id, tooth_number, region_label, image_url,"
            " source_label, recorded_at) values (%s,%s,%s,NULL,%s,%s,now())",
            (rid, patient_id, tooth_number, f"/assets/uploads/{rid}.{ext}",
             "Uploaded sample image — unverified"),
        )
        c.commit()
    return {"record_id": rid, "image_url": f"/assets/uploads/{rid}.{ext}"}


@app.post("/demo/reset")
def demo_reset():
    with get_conn() as c:
        c.execute("truncate table agent_event, investigation_run")
        c.commit()
    return {"ok": True}
