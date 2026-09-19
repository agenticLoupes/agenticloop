---
name: verify-dentassist
description: Launch DentAssist Guardian (FastAPI backend on 8000 + Next.js UI on 3000), run a real pre-procedure investigation against the live Supabase and Gemini, and capture evidence. Use before claiming any backend, agent, or UI change works, before the demo rehearsal, and whenever an investigation "looks stuck".
---

# verify-dentassist

DentAssist Guardian is a web app: a Next.js UI (`frontend/`, port 3000) over a FastAPI agent backend (`backend/`, port 8000) that talks to Supabase Postgres, Gemini, and TypeSafe. Every proof drives the real path: pick a patient, state a procedure, watch the Guardian/Skeptic/Composer trace, read the cards. All patient data is synthetic.

Helper: `.claude/skills/verify-dentassist/scripts/verify.sh <launch|doctor|drive|cleanup>`. It records pids under `.verify/` and writes evidence under `.verify/evidence/<timestamp>/`. Cleanup kills only what launch started and never touches evidence.

## Prerequisites

- `.env` at the repo root with `SUPABASE_DB_URL`, `GOOGLE_API_KEY`, `GEMINI_MODEL`, `TYPESAFE_API_KEY`. The backend reads `backend/.env`; the helper copies the root file there if missing (gitignored).
- A shell that exports its own `GOOGLE_API_KEY` or `GEMINI_API_KEY` will silently override the file: pydantic-settings prefers process env. The helper starts the backend with those unset. If you start it by hand, do the same: `env -u GOOGLE_API_KEY -u GEMINI_API_KEY uvicorn app.main:app`.
- Python 3.12 venv at `backend/.venv` (`uv venv -p 3.12 backend/.venv && uv pip install -p backend/.venv/bin/python -e "backend[dev]" "psycopg[pool]"`). Python 3.14 is not proven. `app/db.py` imports `psycopg_pool`; if `pyproject.toml` still says `psycopg[binary]` (PR 16 changes it to `psycopg[binary,pool]`), install it explicitly.
- Frontend installed with npm against `frontend/package-lock.json`. A bun isolated install breaks Turbopack's postcss resolution.
- Stray top-level directories inside `backend/` (anything beside `app`, `tests`, `scripts`) break the editable install with "Multiple top-level packages discovered".

## Launch

```bash
.claude/skills/verify-dentassist/scripts/verify.sh launch
```

Starts uvicorn on 8000 and `next start` on 3000 from the built `.next` (it runs `npm run build` if `.next` is missing). Ready when `GET :8000/health` returns `{"ok":true,...}` and `GET :3000/` returns 200 with `<title>DentAssist Guardian`. Logs: `.verify/backend.log`, `.verify/frontend.log`.

## Doctor

```bash
.claude/skills/verify-dentassist/scripts/verify.sh doctor
```

Read-only. Confirms: pid files point at live processes we own, `/health` answers, `/demo/patients` returns 12 rows from the live database, the Gemini key in `backend/.env` lists models (HTTP 200), and the configured `GEMINI_MODEL` is in that list. Any red line means do not drive; fix or relaunch.

## Drive

**API path (fast, deterministic handles):**

```bash
.claude/skills/verify-dentassist/scripts/verify.sh drive [PATIENT_ID] [PROCEDURE] [TOOTH]
# default: DEMO-007 extraction 30
```

POSTs `/investigations`, polls `GET /investigations/{run_id}` until `status` is `complete` or `error`, then pulls `/trace`. Passes when status is `complete`, the trace contains `guardian tool_call`, `skeptic decision`, and `composer cards` events, and `final_cards` is non-empty for a scenario patient (DEMO-007 surfaces Warfarin, Penicillin allergy, atrial fibrillation, and one VERIFY on a clinical note).

**Browser path (what a judge sees), with agent-browser:**

```bash
export AGENT_BROWSER_SESSION="$(agent-browser session id --scope worktree --prefix verify)"
agent-browser open http://localhost:3000
agent-browser snapshot -i            # step "patient": one button per patient, name contains the display_name, e.g. "Synthetic Patient 007"
agent-browser click @eN              # the DEMO-007 button
agent-browser snapshot -i            # step "procedure": chips named extraction, filling, crown, root_canal, implant, cleaning; tooth chart has aria-label "Tooth chart — tap a tooth"; one submit button
agent-browser click @e<extraction> && agent-browser click @e<submit>
agent-browser wait --text "Record to review" --timeout 90000   # step "investigating" shows the live trace, then step "results"
agent-browser screenshot .verify/evidence/<ts>/results.png
```

Card titles start with `Record to review —` (SURFACE) or `Item to verify —` (VERIFY). Clicking a card opens the evidence modal (close button has `aria-label="Close"`). A run with nothing to surface lands on the silence screen instead of cards; that is a valid end state, not a failure.

## Evidence

The helper writes to `.verify/evidence/<timestamp>/`: `health.json`, `patients.json`, `investigation.json` (full result with cards and skeptic decisions), `trace.json`, `summary.txt` (pass/fail lines), and the browser screenshot if you took one. Proof standard: a real POST through the public API or a real click path in the UI, the resulting `status`, the trace showing tool calls and skeptic decisions, and the cards. Side effect to check: `SELECT count(*) FROM investigation_run WHERE id = '<run_id>'` on Supabase equals 1 (the helper checks it through `GET /investigations/{run_id}`, which reads that row). Never call `POST /demo/reset` during a proof; it wipes run history the team may be demoing from.

## Cleanup

```bash
.claude/skills/verify-dentassist/scripts/verify.sh cleanup
```

Kills the pids in `.verify/backend.pid` and `.verify/frontend.pid` only, removes the pid files and the browser session you named. Evidence directories stay. Two instances cannot share ports 8000/3000; if doctor shows a port owned by a pid we did not start, stop and say so rather than killing it.

## Feature map

`features/README.md` indexes one file per user-facing feature. A proof that drives one entry point is incomplete when the map lists others. Keep the map honest with `/maintain-verification-skill`.
