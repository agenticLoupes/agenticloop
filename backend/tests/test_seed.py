from app.db import get_conn


def _q(sql, params=None):
    with get_conn() as c:
        return c.execute(sql, params or ()).fetchall()


def test_twelve_patients():
    rows = _q("select count(*) as n from patient")
    assert rows[0]["n"] == 12


def test_demo007_warfarin_active():
    rows = _q(
        "select id, status from medication where patient_id='DEMO-007' and medication_name='Warfarin'"
    )
    assert rows, "DEMO-007 should have a Warfarin medication row"
    assert rows[0]["id"] == "MED-018"
    assert rows[0]["status"] == "active"


def test_demo009_verify_note_without_current_med():
    notes = _q(
        "select summary from clinical_note where patient_id='DEMO-009' and summary ilike %s",
        ("%medication%",),
    )
    meds = _q("select id from medication where patient_id='DEMO-009'")
    assert notes, "DEMO-009 should have a note mentioning a medication change"
    assert not meds, "DEMO-009 should have NO current medication row (drives VERIFY)"


def test_demo008_has_stale_discontinued_med():
    rows = _q("select status from medication where patient_id='DEMO-008' and id='MED-008'")
    assert rows and rows[0]["status"] == "discontinued"


def test_imaging_rows_have_ground_truth_region():
    # Seeded studies carry ground truth; dentist-uploaded X-rays (IMG-UP-*) are
    # VERIFY-only by design and have no region_label, so they are excluded here.
    rows = _q("select id, region_label, image_url from imaging_study where id not like %s order by id", ("IMG-UP-%",))
    ids = {r["id"] for r in rows}
    assert {"IMG-001", "IMG-002", "IMG-003"} <= ids
    for r in rows:
        if r["id"].startswith("IMG-UP-"):
            # uploads deliberately carry NO ground truth -> they can only ever VERIFY
            assert r["region_label"] is None
        else:
            assert r["region_label"], f"{r['id']} missing region_label ground truth"
            assert r["image_url"].endswith(".png")
