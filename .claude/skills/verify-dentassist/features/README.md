# DentAssist Guardian feature map

One file per user-facing feature. Each says what it is, how a user reaches it, how to drive it with the harness (`scripts/verify.sh` for the API, agent-browser for the UI), and what end state proves it. Maintain with `/maintain-verification-skill`.

| Feature | File | Surface |
|---|---|---|
| Pick a patient (with scenario hints) | [patient-select.md](patient-select.md) | UI step `patient`, `GET /demo/patients` |
| State the procedure and tooth | [procedure-form.md](procedure-form.md) | UI step `procedure`, `POST /investigations` |
| Investigation run: trace, cards, silence | [investigation-run.md](investigation-run.md) | UI steps `investigating` → `results`, `GET /investigations/{id}`, `/trace` |
| Evidence modal and X-ray upload | [evidence-and-imaging.md](evidence-and-imaging.md) | Card click, `GET /evidence/{type}/{id}`, `/assets` |

Not mapped yet: `POST /demo/reset` (destructive; never drive during a proof), `GET /patients/{id}`.
