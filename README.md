# DentAssist Guardian

DentAssist Guardian is an autonomous pre-procedure record-review prototype. A dentist states a procedure, and the Guardian investigates the patient's synthetic medical and dental record for evidence worth reviewing. The Skeptic challenges each candidate before the app shows a source-backed card or stays silent.

> **Synthetic data prototype:** DentAssist Guardian is a proof of concept, not a diagnostic device. The dentist remains the decision-maker.

## Quick start

You need Python 3.12, [`uv`](https://docs.astral.sh/uv/), and Node.js with npm.

Clone the repository and create the backend environment file:

```bash
git clone https://github.com/agenticLoupes/agenticloop.git && cd agenticloop
cp backend/.env.example backend/.env
```

Open `backend/.env` and set `SUPABASE_DB_URL`, `GOOGLE_API_KEY`, `GEMINI_MODEL`, and `TYPESAFE_API_KEY`. Use a Supabase session-pooler URL. The backend reads `backend/.env` because the server starts from the `backend` directory.

Install the backend and frontend dependencies:

```bash
uv venv -p 3.12 backend/.venv
uv pip install -p backend/.venv/bin/python -e "backend[dev]"
(cd frontend && npm ci && npm run build)
```

Use npm for the frontend. Bun's isolated dependency layout breaks Turbopack's PostCSS resolution in this project.

Start the backend in one terminal:

```bash
(cd backend && .venv/bin/uvicorn app.main:app --port 8000)
```

Start the frontend in a second terminal:

```bash
(cd frontend && npm run start)
```

Open [http://localhost:3000](http://localhost:3000). The backend health endpoint is [http://localhost:8000/health](http://localhost:8000/health).

If your shell exports `GOOGLE_API_KEY` or `GEMINI_API_KEY`, that value overrides `backend/.env`. Unset those variables before a manual launch or use the verification helper, which unsets them for the backend process.

For a one-command proof, copy `.env.example` to `.env`, fill in the four values, and run:

```bash
.claude/skills/verify-dentassist/scripts/verify.sh launch
.claude/skills/verify-dentassist/scripts/verify.sh doctor
.claude/skills/verify-dentassist/scripts/verify.sh drive
```

The helper records logs and evidence under `.verify/`. Run `.claude/skills/verify-dentassist/scripts/verify.sh cleanup` when finished.

## Tech stack and architecture

- Next.js 16, React 19, TypeScript, and Tailwind CSS provide the browser interface.
- FastAPI provides the HTTP API.
- LangGraph coordinates the Context Interpreter, Guardian, Skeptic, and Composer.
- Gemini drives the Guardian's ReAct investigation. `GEMINI_MODEL` selects the model, and the repository default is `gemini-2.5-flash`.
- TypeSafe Jev returns the Skeptic's `SURFACE`, `DISMISS`, or `VERIFY` decision.
- Supabase Postgres stores synthetic records, investigation runs, and agent events in 10 tables, including imaging and conversation transcripts.

```text
Browser (Next.js 16)
        |
        v
FastAPI API
        |
        v
LangGraph
  Context Interpreter
        |
        v
  Guardian Investigator
  Gemini ReAct over 9 record-query tools
        |
        v
  Skeptic / Verifier
  TypeSafe Jev: SURFACE | DISMISS | VERIFY
        |
        v
  Assist Composer
        |
        v
Evidence-backed cards

Guardian tools ----------------> Supabase Postgres
  9 record-query tools             10 tables
  read_imaging vision tool         imaging + transcripts
```

The Guardian chooses which tools to call and can change its next step after a finding. Every factual card cites a record ID that the dentist can open. The Composer formats accepted evidence and does not add medical advice.

## Reproduce the demo

Start both services, open the app, select a patient, choose the procedure and tooth, and press **Challenge procedure**.

| Scenario | Input | Expected result |
| --- | --- | --- |
| A, surface | `DEMO-007`, extraction, tooth `30` | The verified run surfaced Warfarin `MED-018`, Penicillin allergy `ALG-007`, and atrial fibrillation `COND-007A` in 17 seconds. |
| B, dismiss | `DEMO-008`, extraction, tooth `3` | The seeded case has only a discontinued medication and a resolved condition. The Skeptic dismisses the candidates or the app shows the silence screen. |
| C, verify | `DEMO-009`, extraction, tooth `19` | Note `NOTE-009` reports a blood-thinner change without a current medication row, so the current status requires verification. |

You can drive any scenario through the public API and save its trace:

```bash
.claude/skills/verify-dentassist/scripts/verify.sh drive DEMO-007 extraction 30
.claude/skills/verify-dentassist/scripts/verify.sh drive DEMO-008 extraction 3
.claude/skills/verify-dentassist/scripts/verify.sh drive DEMO-009 extraction 19
```

Scenario A is the latest verified run recorded in issue #18. The full live sweep for all seeded patients is tracked in [issue #22](https://github.com/agenticLoupes/agenticloop/issues/22).

## Data and provenance

All patient identities and structured medical and dental records are hand-authored synthetic data. They contain no protected health information. Synthea was considered but was not imported. DENTEX was rejected because its non-commercial license did not fit the project.

The seeded radiographs are synthetic renders generated by `db/make_images.py`. The repository also contains upload fixtures. See [docs/PROVENANCE.md](docs/PROVENANCE.md) for per-file authorship, dates, licenses, and the open provenance gap for one uploaded image.

## Known limitations and next steps

- Gemini's tool selection and reasoning have not been validated on real clinical records.
- The Skeptic is an LLM judge, not a clinical rule engine.
- Uploaded X-rays have no authored ground truth and can only produce `VERIFY` results.
- The prototype has no authentication, audit log, or de-identifying gateway.
- The app uses a single-tenant demo database.
- DentAssist Guardian is a proof of concept, not a diagnostic device.

Before clinical use, the system needs prospective validation, security and privacy controls, tenant isolation, auditability, and integration with governed clinical data sources.
