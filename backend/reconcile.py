"""The autonomous divergence check.  [OWNER: C]  plan.md §1, never cut.

Runs after every turn, unprompted. Compares what was just logged for a tooth
against its history and raises ONE flag row when something new diverges.

    reconcile(session_id, patient_id, tooth, about_to=None) -> Flag | None

Four checks, each a `kind`:
  perio_worsening   latest pocket depth > earliest depth in the last 12 months
  restoration_age   amalgam > 12 yrs or composite > 7 yrs        (info)
  symptom_pattern   a sensitivity/pain finding this session on a tooth that
                    also has an open-margin note or perio_worsening   (watch)
  allergy           about_to in ANESTHESIA_MOMENTS and allergies on file (stop)

Cooldown: kinds already flagged for (session, tooth) never fire again. The
`flags.kind` column stores the comma-joined kinds of each row; the UNIQUE
index is the backstop. At an anesthesia moment the new flag recaps earlier
flags on the tooth so the spoken line carries the whole picture once.
"""
from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta

from numbering import spoken
from schemas import Flag
from tools._db import connect, loads, rows

ANESTHESIA_MOMENTS = {"anesthesia", "antibiotic", "prescription", "numb"}
_SYMPTOM = re.compile(r"sensitiv|pain|ache|hurt|tender|throb", re.I)
_MARGIN = re.compile(r"open|margin|catch|stain", re.I)
_SEVERITY_RANK = {"info": 0, "watch": 1, "stop": 2}
_TRIGGER_WORDS = re.compile(r"\b(numb|anesth|inject|lidocaine|carbocaine|prescri|antibiotic|amoxicillin|penicillin)", re.I)


def about_to_from_transcript(transcript: str) -> str | None:
    """'hey loupes, ready to numb' -> 'anesthesia'. Cheap keyword gate for A3."""
    m = _TRIGGER_WORDS.search(transcript or "")
    if not m:
        return None
    w = m.group(1).lower()
    if w.startswith(("prescri", "antibiotic", "amox", "penic")):
        return "antibiotic"
    return "anesthesia"


def _month(d: str) -> str:
    return datetime.fromisoformat(d).strftime("%B %Y")


def _years_since(d: str | None, today: date) -> float | None:
    if not d:
        return None
    return (today - date.fromisoformat(d)).days / 365.25


def _checks(conn, session_id: str, patient_id: str, fdi: str, about_to: str | None,
            today: date) -> list[dict]:
    """Return every check that fires as {kind, severity, message, basis}."""
    out: list[dict] = []
    say = spoken(fdi)

    tooth = conn.execute("SELECT * FROM teeth WHERE patient_id=? AND tooth=?",
                         (patient_id, fdi)).fetchone()
    patient = conn.execute("SELECT allergies FROM patients WHERE id=?", (patient_id,)).fetchone()
    perio = rows(conn.execute(
        "SELECT periodontal_depth_mm AS mm, measured_on FROM perio_history "
        "WHERE patient_id=? AND tooth=? AND measured_on >= ? ORDER BY measured_on",
        (patient_id, fdi, (today - timedelta(days=366)).isoformat())))
    findings = rows(conn.execute(
        "SELECT id, observation, source FROM session_findings "
        "WHERE session_id=? AND patient_id=? AND tooth=? ORDER BY id", (session_id, patient_id, fdi)))

    worsening = False
    if len(perio) >= 2 and perio[-1]["mm"] > perio[0]["mm"]:
        worsening = True
        out.append({
            "kind": "perio_worsening", "severity": "watch",
            "message": f"Pocket depth on {say} went {perio[0]['mm']} to {perio[-1]['mm']} millimeters since {_month(perio[0]['measured_on'])}.",
            "basis": [f"history:perio:{perio[0]['measured_on']}", f"history:perio:{perio[-1]['measured_on']}"],
        })

    if tooth and tooth["restoration"]:
        age = _years_since(tooth["last_treated"], today)
        r = tooth["restoration"].lower()
        limit = 12 if "amalgam" in r else 7 if "composite" in r else None
        if age is not None and limit is not None and age > limit:
            out.append({
                "kind": "restoration_age", "severity": "info",
                "message": f"The {r.split(',')[0]} on {say} is {int(age)} years old, past the {limit}-year expected life.",
                "basis": [f"history:restoration:{tooth['last_treated']}"],
            })

    symptomatic = [f for f in findings if _SYMPTOM.search(f["observation"])]
    margin_note = bool(tooth and tooth["notes"] and _MARGIN.search(tooth["notes"]))
    if symptomatic and (margin_note or worsening):
        f = symptomatic[-1]
        why = "the distal margin was already on watch" if margin_note else "the pocket is deepening"
        out.append({
            "kind": "symptom_pattern", "severity": "watch",
            "message": f"You logged {f['observation'].rstrip('.')} on {say} this session, and {why}.",
            "basis": [f"finding:{f['id']}"] + ([f"history:notes"] if margin_note else []),
        })

    allergies = loads(patient["allergies"], []) if patient else []
    if about_to in ANESTHESIA_MOMENTS and allergies:
        out.append({
            "kind": "allergy", "severity": "stop",
            "message": f"{', '.join(a.capitalize() for a in allergies)} allergy on file.",
            "basis": ["history:allergies"],
        })
    return out


def reconcile(session_id: str, patient_id: str, tooth: str, about_to: str | None = None,
              today: date | None = None) -> Flag | None:
    from tools.tooth_record import normalize_tooth  # local import: avoids a cycle at package load

    fdi = normalize_tooth(tooth)
    today = today or date.today()
    conn = connect()
    try:
        prior = rows(conn.execute(
            "SELECT id, kind, message FROM flags WHERE session_id=? AND tooth=? ORDER BY id",
            (session_id, fdi)))
        already = {k for p in prior for k in p["kind"].split(",")}
        fired = [c for c in _checks(conn, session_id, patient_id, fdi, about_to, today)
                 if c["kind"] not in already]
        if not fired:
            return None

        severity = max((c["severity"] for c in fired), key=_SEVERITY_RANK.__getitem__)
        parts = [c["message"] for c in fired]
        basis = [b for c in fired for b in c["basis"]]
        if about_to in ANESTHESIA_MOMENTS and prior:
            parts.append("Earlier this session: " + " ".join(p["message"] for p in prior))
            basis += [f"flag:{p['id']}" for p in prior]
        lead = "Before you numb: " if about_to in ANESTHESIA_MOMENTS else ""
        message = lead + " Also, ".join(parts) if len(parts) > 1 else lead + parts[0]
        kind = ",".join(c["kind"] for c in fired)

        cur = conn.execute(
            "INSERT OR IGNORE INTO flags (session_id, patient_id, tooth, kind, severity, message, basis) "
            "VALUES (?,?,?,?,?,?,?)",
            (session_id, patient_id, fdi, kind, severity, message, json.dumps(basis)))
        conn.commit()
        if cur.rowcount == 0:
            return None
        row = conn.execute("SELECT * FROM flags WHERE id=?", (cur.lastrowid,)).fetchone()
    finally:
        conn.close()

    return Flag(id=row["id"], tooth=row["tooth"], severity=row["severity"], message=row["message"],
                basis=json.loads(row["basis"]), created_at=row["created_at"])


def list_flags(session_id: str, since: int = 0) -> list[Flag]:
    """GET /flags backing query. Rows with id > since, oldest first."""
    conn = connect()
    try:
        rs = rows(conn.execute(
            "SELECT * FROM flags WHERE session_id=? AND id>? ORDER BY id", (session_id, since)))
    finally:
        conn.close()
    return [Flag(id=r["id"], tooth=r["tooth"], severity=r["severity"], message=r["message"],
                 basis=json.loads(r["basis"]), created_at=r["created_at"]) for r in rs]
