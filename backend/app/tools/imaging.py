"""Imaging tools. get_imaging is deterministic; read_imaging is vision (locate + relevance ONLY).

read_imaging never diagnoses. Its reported region is validated against the authored
region_label ground truth: agreement -> usable; disagreement/uncertainty -> uncertain
(the Skeptic then VERIFYs/DISMISSes). A vision hallucination cannot become a false SURFACE.
"""
import base64
from pathlib import Path
from typing import Optional

from app.db import get_conn
from app.tools.records import _to_record, get_record
from app.models import Record

ASSETS_ROOT = Path(__file__).resolve().parents[3] / "db"


def get_imaging(patient_id: str, tooth_number: Optional[int] = None) -> list[Record]:
    sql = "select * from imaging_study where patient_id = %s"
    params: list = [patient_id]
    if tooth_number is not None:
        sql += " and tooth_number = %s"
        params.append(tooth_number)
    sql += " order by recorded_at desc nulls last"
    with get_conn() as c:
        rows = c.execute(sql, tuple(params)).fetchall()
    return [_to_record(r, "imaging") for r in rows]


def read_imaging(record_id: str, procedure: str, tooth_number: Optional[int] = None) -> dict:
    """Vision locate + relevance on an imaging record. Returns a neutral observation dict.

    {region_reported, region_label, region_match, relevant, uncertain, evidence_id}
    """
    rec = get_record("imaging", record_id)
    if rec is None:
        return {"error": f"imaging record {record_id} not found", "uncertain": True}

    img_path = ASSETS_ROOT / rec.data["image_url"].lstrip("/")
    if not img_path.exists():
        return {"error": f"image file missing for {record_id}", "uncertain": True,
                "evidence_id": record_id}

    from langchain_core.messages import HumanMessage
    from app.provider import get_llm

    b64 = base64.b64encode(img_path.read_bytes()).decode()
    prompt = (
        "You are locating a dental imaging record. Do NOT diagnose, do NOT identify pathology. "
        f"State only: (1) which tooth region this image covers, (2) whether it is relevant to a "
        f"'{procedure}' at tooth #{tooth_number}. Reply as two short lines: "
        "REGION: <region description>\nRELEVANT: yes|no|unclear"
    )
    msg = HumanMessage(content=[
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
    ])
    try:
        out = get_llm().invoke([msg])
        content = out.content
        if isinstance(content, list):  # Gemini returns a list of content parts
            text = "\n".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in content)
        else:
            text = str(content)
    except Exception as e:  # provider failure -> uncertain, never invented (§22)
        return {"error": f"vision unavailable: {e}", "uncertain": True, "evidence_id": record_id}

    reported = ""
    relevant = "unclear"
    for line in text.splitlines():
        low = line.lower()
        if "region:" in low:
            reported = line.split(":", 1)[1].strip()
        if "relevant:" in low:
            relevant = line.split(":", 1)[1].strip().lower()

    truth = rec.data["region_label"]
    # ground-truth gate: tooth number in the authored label must appear in the report (or vice versa)
    match = bool(reported) and any(
        tok in reported.lower() for tok in truth.lower().replace("—", " ").split() if tok.startswith("#")
    ) or (truth.lower()[:12] in reported.lower())
    return {
        "evidence_id": record_id,
        "region_reported": reported,
        "region_label": truth,
        "region_match": match,
        "relevant": relevant == "yes",
        "uncertain": (relevant == "unclear") or not match,
    }
