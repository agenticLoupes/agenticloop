"""GATE 1 (spec §25): the tool/data layer can retrieve every expected source record by ID.

Every evidence id referenced by the demo scenarios (db/scenarios.md) must resolve to a
non-null Record whose patient_id matches. This is the evidence contract's foundation (§12):
no card may cite an evidence id that does not open a real synthetic record.
"""
import pytest

from app.tools.records import get_record

# (record_type, record_id, expected_patient_id) — the evidence the demo relies on.
SCENARIO_EVIDENCE = [
    ("medication", "MED-018", "DEMO-007"),      # SURFACE: active Warfarin
    ("allergy", "ALG-007", "DEMO-007"),         # SURFACE: Penicillin allergy
    ("medication", "MED-008", "DEMO-008"),      # DISMISS: stale discontinued med
    ("clinical_note", "NOTE-009", "DEMO-009"),  # VERIFY: reported med change, no current status
    ("imaging", "IMG-001", "DEMO-010"),         # imaging SURFACE (#30 region)
    ("imaging", "IMG-002", "DEMO-010"),         # imaging DISMISS (#3 region)
    ("imaging", "IMG-003", "DEMO-009"),         # imaging VERIFY (low detail)
    ("dental_event", "DENT-007A", "DEMO-007"),  # tooth #30 history
    ("conversation", "CONV-007", "DEMO-007"),   # transcript: reports stopping anticoagulant
]


@pytest.mark.parametrize("record_type,record_id,patient_id", SCENARIO_EVIDENCE)
def test_scenario_evidence_retrievable(record_type, record_id, patient_id):
    r = get_record(record_type, record_id)
    assert r is not None, f"GATE 1 FAIL: {record_type}/{record_id} not retrievable"
    assert r.patient_id == patient_id, f"{record_id} belongs to {r.patient_id}, expected {patient_id}"
    assert r.record_id == record_id
