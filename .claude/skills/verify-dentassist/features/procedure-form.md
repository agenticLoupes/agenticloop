# State the procedure and tooth

Second screen. Procedure chips (`extraction`, `filling`, `crown`, `root_canal`, `implant`, `cleaning`), a visual tooth chart (`aria-label="Tooth chart — tap a tooth"`, Universal numbering 1–32), a three step explainer, and a submit button. Submitting calls `POST /investigations` and moves to the investigating step.

## Sub-features
- Procedure chips (single select)
- Tooth chart picker, optional
- Scenario pre-fill when the patient carried a suggestion
- Submit → `POST /investigations {patient_id, procedure, tooth_number}` → `{run_id, status:"running"}`

## How to get to it (user POV)
Pick a patient on the first screen.

## Driving it with agent-browser / curl
- API: `verify.sh drive DEMO-007 extraction 30` (or any patient, procedure, tooth).
- UI: after selecting a patient, `agent-browser snapshot -i`; click the chip named `extraction`, optionally a tooth in the chart, then the `submit` button. Re-snapshot: the live trace view is showing.

## Gotchas
- Unknown `patient_id` returns HTTP 400 from `POST /investigations` (`start_run` rejects it) and the UI lands on the error step.
- `tooth_number` is optional; omit it for whole-mouth procedures like `cleaning`.
