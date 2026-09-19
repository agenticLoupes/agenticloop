"""Acceptance for C1 (#8) and C2 (#9) against a fresh seeded SQLite file.

Run from backend/:  pytest -q
"""
from __future__ import annotations

import os
import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

DEMO_DAY = date(2026, 9, 19)


@pytest.fixture()
def db(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "loupes.db"))
    yield


def test_numbering_roundtrip():
    from numbering import fdi_to_universal, parse_tooth, spoken, universal_to_fdi
    assert universal_to_fdi("19") == "36"
    assert fdi_to_universal("36") == "19"
    assert parse_tooth("nineteen") == "36"
    assert parse_tooth("tooth 30 please") == "46"
    assert parse_tooth("36") == "36"
    assert spoken("36") == "nineteen"
    assert spoken("46") == "thirty"


def test_get_tooth_record_returns_demo_facts(db):
    from tools.tooth_record import get_tooth_record
    rec = get_tooth_record("19", "P-88204")          # universal in, FDI stored
    assert rec["tooth"] == "36" and rec["found"]
    assert rec["restoration"].startswith("composite")
    assert rec["last_treated"] == "2024-02-14"
    assert rec["periodontal_depth_mm"] == 4
    assert [p["periodontal_depth_mm"] for p in rec["perio_history"]] == [3, 3, 4]
    assert rec["patient_allergies"] == ["penicillin"]
    assert rec["recent_findings"] == []


def test_log_finding_persists_and_is_read_back(db):
    from tools.log_finding import log_finding
    from tools.tooth_record import get_tooth_record
    out = log_finding("36", "patient reports cold sensitivity", "patient_speech", 0.9, "demo-1", "P-88204")
    assert out["id"] >= 1
    rec = get_tooth_record("36", "P-88204")
    assert rec["recent_findings"][0]["observation"] == "patient reports cold sensitivity"
    assert rec["recent_findings"][0]["source"] == "patient_speech"
    with pytest.raises(ValueError):
        log_finding("36", "x", "rumor", 0.5, "demo-1", "P-88204")


def test_reconcile_demo_sequence(db):
    """Step 4 logs sensitivity -> watch flag with worsening + symptom.
    Step 6 'ready to numb' -> stop flag with allergy plus a recap. Then silence."""
    from reconcile import about_to_from_transcript, list_flags, reconcile
    from tools.log_finding import log_finding

    log_finding("36", "patient reports cold sensitivity", "patient_speech", 0.9, "demo-1", "P-88204")

    first = reconcile("demo-1", "P-88204", "36", today=DEMO_DAY)
    assert first is not None
    assert first.severity == "watch"
    assert "3 to 4 millimeters" in first.message and "March 2026" in first.message
    assert "cold sensitivity" in first.message
    assert any(b.startswith("finding:") for b in first.basis)
    assert "penicillin" not in first.message.lower()

    assert reconcile("demo-1", "P-88204", "36", today=DEMO_DAY) is None   # cooldown

    assert about_to_from_transcript("ready to numb") == "anesthesia"
    second = reconcile("demo-1", "P-88204", "36", about_to="anesthesia", today=DEMO_DAY)
    assert second is not None and second.severity == "stop"
    assert second.message.startswith("Before you numb")
    assert "Penicillin allergy on file" in second.message
    assert "3 to 4 millimeters" in second.message            # recap of the earlier flag
    assert f"flag:{first.id}" in second.basis

    assert reconcile("demo-1", "P-88204", "36", about_to="anesthesia", today=DEMO_DAY) is None
    assert [f.id for f in list_flags("demo-1")] == [first.id, second.id]
    assert list_flags("demo-1", since=first.id) == [second]


def test_reconcile_quiet_on_healthy_tooth(db):
    from reconcile import reconcile
    assert reconcile("demo-1", "P-88204", "26", today=DEMO_DAY) is None     # crown 2022, stable 2 mm


def test_restoration_age_fires_on_old_amalgam(db):
    from reconcile import reconcile
    f = reconcile("demo-1", "P-88204", "30", today=DEMO_DAY)   # universal 30 = FDI 46, amalgam 2011
    assert f is not None and f.severity == "info" and "amalgam" in f.message and "thirty" in f.message
