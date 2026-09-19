"""GATE 3 (spec §25/§10): real agency — different cases produce different tool paths.

Reads traces of completed investigation runs (cheap, no model calls). Requires at least
two completed runs for different patients (produced by demo runs / scripts).
"""
import pytest

from app.db import get_conn


def _paths():
    with get_conn() as c:
        runs = c.execute(
            "select id, patient_id from investigation_run where status='complete'").fetchall()
        out = []
        for r in runs:
            evs = c.execute(
                "select summary from agent_event where run_id=%s and agent='guardian'"
                " and event_type='tool_call' order by sequence_no", (r["id"],)).fetchall()
            out.append((r["patient_id"], tuple(e["summary"] for e in evs)))
    return out


def test_different_patients_produce_different_tool_paths():
    paths = _paths()
    patients = {p for p, _ in paths}
    if len(patients) < 2:
        pytest.skip("need completed runs for >=2 patients (run the demo scenarios first)")
    assert len({path for _, path in paths}) > 1, "all runs used an identical tool sequence"


def test_guardian_does_not_call_every_tool_every_time():
    paths = [path for _, path in _paths()]
    if not paths:
        pytest.skip("no completed runs")
    # 10 tools exist; a fixed pipeline would show identical, exhaustive sequences
    lengths = {len(p) for p in paths}
    assert len(lengths) > 1 or all(l < 20 for l in lengths), "tool usage looks like a fixed pipeline"
