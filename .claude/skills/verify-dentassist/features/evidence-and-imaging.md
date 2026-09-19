# Evidence modal and X-ray upload

Every card cites `evidence_ids`. Clicking a card opens the evidence modal, which fetches `GET /evidence/{record_type}/{record_id}` and shows the source row; imaging records render the radiograph inline from `/assets/...`. A separate X-ray upload path adds an imaging row with no ground truth region; the Guardian may cite it only as VERIFY.

## Sub-features
- Evidence modal per card (`aria-label="Close"` to dismiss)
- Inline radiograph on imaging cards
- X-ray upload (VERIFY-only)
- Static assets served from `db/assets` at `/assets`

## How to get to it (user POV)
Reach the results step, click any card.

## Driving it with agent-browser / curl
- API: take an `evidence_ids` entry from `investigation.json`, e.g. `MED-018`, and the matching record type from `backend/app/tools/records.py` `TYPE_CONFIG`; `curl -s localhost:8000/evidence/medication/MED-018` returns the row. Imaging: `curl -sI localhost:8000/assets/<file>` returns 200 for a seeded image.
- UI: on results, `agent-browser snapshot -i`, click a card, re-snapshot to see the modal contents, then click the `Close` button.

## Gotchas
- Uploaded imaging rows (`IMG-UP-…`) have `region_label` NULL by design; `tests/test_seed.py::test_imaging_rows_have_ground_truth_region` currently fails on them and needs to filter to seeded `IMG-0xx` rows.
- `/assets` mounts `db/assets`; a missing directory fails app startup.
