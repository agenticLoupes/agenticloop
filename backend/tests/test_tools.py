from app.tools import records, imaging
from app.models import Record


def test_get_record_medication():
    r = records.get_record("medication", "MED-018")
    assert isinstance(r, Record)
    assert r.record_id == "MED-018"
    assert r.patient_id == "DEMO-007"
    assert r.data["medication_name"] == "Warfarin"


def test_get_record_unknown_returns_none():
    assert records.get_record("medication", "MED-DOESNOTEXIST") is None


def test_get_patient_summary():
    r = records.get_patient_summary("DEMO-007")
    assert r is not None and r.record_type == "patient" and r.patient_id == "DEMO-007"


def test_get_dental_history_by_tooth():
    rs = records.get_dental_history("DEMO-007", tooth_number=30)
    ids = {r.record_id for r in rs}
    assert {"DENT-007A", "DENT-007B"} <= ids
    assert "DENT-007C" not in ids  # tooth #14, filtered out


def test_get_active_medications_excludes_discontinued():
    rs = records.get_active_medications("DEMO-008")
    assert rs == []  # DEMO-008's only med is discontinued
    rs7 = records.get_active_medications("DEMO-007")
    assert {r.data["medication_name"] for r in rs7} == {"Warfarin", "Cetirizine"}


def test_get_medication_history_named():
    rs = records.get_medication_history("DEMO-008", medication_name="Amoxicillin")
    assert [r.record_id for r in rs] == ["MED-008"]
    assert rs[0].data["status"] == "discontinued"


def test_get_allergies():
    rs = records.get_allergies("DEMO-007")
    assert any(r.data["substance"] == "Penicillin" for r in rs)


def test_get_medical_conditions_active_only():
    rs = records.get_medical_conditions("DEMO-007", status="active")
    names = {r.data["condition_name"] for r in rs}
    assert names == {"Atrial fibrillation"}  # resolved knee replacement excluded


def test_search_clinical_notes():
    rs = records.search_clinical_notes("DEMO-009", query="medication")
    assert [r.record_id for r in rs] == ["NOTE-009"]


def test_get_imaging_all_and_by_tooth():
    all_imgs = {r.record_id for r in imaging.get_imaging("DEMO-010")}
    assert {"IMG-001", "IMG-002"} <= all_imgs
    by_tooth = {r.record_id for r in imaging.get_imaging("DEMO-010", tooth_number=30)}
    assert by_tooth == {"IMG-001"}
