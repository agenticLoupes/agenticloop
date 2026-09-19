# DentAssist Guardian Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an autonomous pre-procedure record-review agent that investigates a synthetic dental/medical record, challenges its own findings, and surfaces only source-backed records worth reviewing.

**Architecture:** Next.js (mobile-first) → FastAPI → LangGraph orchestrating four agents (Context Interpreter, Guardian Investigator, Skeptic/Verifier, Assist Composer) over a deterministic tool layer that reads synthetic patient records — including synthetic radiographs — from Supabase Postgres. A vision-capable model supplies the Guardian's tool-calling; **Jev (TypeSafe) supplies the Skeptic's decisions**. A **procedure playbook** (static, authored) steers *which* records the Guardian investigates (pattern-informed investigation), without ever producing advice. State is explicit application state, never hidden conversation history.

**Tech Stack:** Next.js 15 (App Router, TypeScript), Tailwind CSS, FastAPI, Python 3.11+, LangGraph, **Google Gemini (gemini-2.5-flash, vision + tool-calling) via Google AI Studio for the Guardian's tool-selection *and* `read_imaging` vision** (`langchain-google-genai`), **TypeSafe/Jev (System One) for the Skeptic/Verifier decisions**, Supabase Postgres, pytest.

**Stack override (user instruction, supersedes §32):**
1. **Provider = Google Gemini (free Google AI Studio tier), not Featherless/OpenAI.** The hackathon does not require Featherless; one `gemini-2.5-flash` model serves both the Guardian's tool-calling and the vision `read_imaging` (multimodal), and the AI Studio free tier keeps demo cost at zero. One provider, one key, server-side only (§14). `gemini-2.5-pro` is the drop-in upgrade if flash underperforms on tool-calling.
2. **Decisions = Jev.** The Skeptic/Verifier (§9.3) decision `SURFACE | DISMISS | VERIFY` is a TypeSafe **Choice**, and its 8 checks are TypeSafe **Noul** judgments — not free-text LLM output. Removes a class of "invented certainty" failure.

**Spec:** `PLAN.md` (frozen MVP master plan — this plan argues from it; executors read both). Section references below (`§N`) point into `PLAN.md`.

## Global Constraints

Every task's requirements implicitly include this section. Values copied verbatim from the spec.

- **Data is 100% synthetic.** UI must always show the label `SYNTHETIC DATA — PROTOTYPE` (§7). Never imply real patients.
- **Evidence contract (§12):** `NO EVIDENCE ID → NO FACTUAL CARD`. Every candidate and surfaced card carries `evidence_ids`; clicking a card must open the underlying synthetic record.
- **No diagnosis / no treatment / no prescription / no clinical advice** output, ever (§6 "Do not build", §21, §30). No agent tells the dentist or patient what to *do*.
- **Pattern-informed investigation is steering, not advice (user-approved "Reading A").** The `procedure_playbook` maps a procedure → record *categories* commonly worth investigating (e.g. extraction → medications/allergies/bleeding-risk conditions/tooth history). It only influences *which of the patient's own records the Guardian inspects and surfaces*. It NEVER emits a recommendation. Its only user-visible trace is a `reason_shown` explaining *why a record was surfaced* ("medications are commonly relevant to extractions") — never *what to do*. `healthcare-reviewer` polices this at Gate 2.
- **Vision is locate + relevance only (user-approved).** `read_imaging` identifies the region/tooth an image covers and whether it is relevant to the procedure. It does NOT identify a cause, finding, or diagnosis (§21). Images are synthetic with authored ground-truth labels; the model's output is validated against the label, so a vision hallucination can only degrade to VERIFY/DISMISS — never a false SURFACE.
- **Safe product language only (§21).** Use "Record to review", "Item to verify", "Relevant record located", "Selected during pre-procedure review", "Source evidence", "Current status could not be established", "No additional record surfaced". Avoid "Unsafe procedure", "Do not perform", "Diagnosis", "You should prescribe", "Recommended treatment", "definitely has", "Clinically validated", "HIPAA compliant".
- **No confidence percentages** (§9.3). Decisions are `SURFACE | DISMISS | VERIFY` only. The decision comes from a TypeSafe **Choice** (its distribution stays internal; no % shown to the dentist per §21). The 8 skeptic checks (§9.3) are TypeSafe **Noul** judgments over the candidate + its evidence `Record`s.
- **The LLM never invents patient facts** (§11). All facts originate from deterministic tool results that carry a `record_id`.
- **Agent is not a fixed pipeline (§10).** Tool order must be model-chosen; different scenarios must produce different tool paths (Gate 3).
- **Do not expose the model API key in the browser** (§14). Gemini (and Jev) are called server-side (FastAPI) only.
- **No custom realtime/WebSocket/SSE infrastructure** (§6). Trace is returned with the result or via lightweight polling (§15).
- **Failure behavior table (§22) is normative.** Silence is a valid successful outcome.
- **Frozen rule (§32):** do not redesign the product mid-build unless a technical blocker makes the core loop impossible.
- **Time-priority order if crunched (§26):** agent investigation > evidence correctness > SURFACE/DISMISS/VERIFY > working UI > agent trace > deployment > visual polish > integrations.

---

## Repository File Structure

```
DentAssist-Guardian/
├── PLAN.md                         # frozen spec (source of truth)
├── README.md                       # quick-start (Phase 6)
├── .env.example                    # all required env vars, no secrets (Phase 6)
├── .gitignore
├── docs/
│   └── superpowers/plans/…         # this plan
├── db/
│   ├── schema.sql                  # 8 tables (§17)
│   ├── seed.sql                    # 12 synthetic patients + scenarios (§7, §8)
│   └── scenarios.md               # human-readable map: which patient proves which outcome
├── backend/
│   ├── pyproject.toml
│   ├── app/
│   │   ├── main.py                 # FastAPI app + routes (§16)
│   │   ├── config.py               # env/settings (Supabase, Gemini, TypeSafe)
│   │   ├── db.py                   # connection/pool
│   │   ├── models.py               # pydantic: Record, InvestigationState, Candidate, Card, AgentEvent
│   │   ├── playbook.py             # procedure → record-category map (pattern-informed steering)
│   │   ├── tools/
│   │   │   ├── __init__.py          # tool registry + JSON schemas (§11)
│   │   │   ├── records.py           # the 8 deterministic query functions
│   │   │   └── imaging.py           # get_imaging (deterministic) + read_imaging (vision + ground-truth gate)
│   │   ├── agents/
│   │   │   ├── context_interpreter.py   # §9.1
│   │   │   ├── guardian.py              # §9.2
│   │   │   ├── skeptic.py               # §9.3
│   │   │   └── composer.py              # §9.4
│   │   ├── graph.py                # LangGraph assembly (§14, §10)
│   │   ├── provider.py             # Gemini vision+tool-calling adapter (Guardian + read_imaging)
│   │   ├── jev.py                  # TypeSafe/Jev wrapper (Skeptic decisions)
│   │   └── trace.py                # AgentEvent recording
│   └── tests/
│       ├── conftest.py             # seeded DB fixture
│       ├── test_tools.py           # Gate 1
│       ├── test_agents.py          # Gate 2
│       └── test_agency.py          # Gate 3 (different tool paths)
└── frontend/                       # Next.js (Phase 4)
    ├── package.json
    ├── app/                        # 5 screens (§20)
    ├── components/                 # PatientSelector, ProcedureForm, AgentTrace, ResultCard, EvidenceDrawer, SyntheticBanner
    └── lib/api.ts                  # typed client for the minimal API (§16)
```

**Boundary rationale:** `tools/records.py` is the *only* code that reads patient rows — agents receive its typed results, never raw SQL. `graph.py` owns control flow; agent modules own single-responsibility prompting/decisions. Frontend never talks to Gemini, Jev, or Supabase directly — only to FastAPI.

---

# PHASE 1 — DATA (detailed)

**Deliverable:** Supabase schema + 12 synthetic patients covering SURFACE/DISMISS/VERIFY + a deterministic Python tool layer that retrieves every expected record by ID.

**Gate 1 (§25):** The API/tool layer can retrieve every expected source record by ID.

**Prerequisites (user-provided before execution):**
- Supabase project created; `SUPABASE_DB_URL` (direct Postgres connection string) available.
- These land in `backend/.env` (gitignored). `.env.example` documents them.

### Task 1.1: Backend project scaffold + config

**Files:**
- Create: `backend/pyproject.toml`, `backend/app/__init__.py`, `backend/app/config.py`, `backend/.env.example`, `backend/.gitignore`
- Test: `backend/tests/test_config.py`

**Interfaces:**
- Produces: `app.config.Settings` (pydantic-settings) with `supabase_db_url: str`, `google_api_key: str`, `gemini_model: str = "gemini-2.5-flash"`, `typesafe_api_key: str`. `get_settings() -> Settings` (cached).

- [ ] **Step 1: Write the failing test**
```python
# backend/tests/test_config.py
import os
from app.config import get_settings

def test_settings_reads_env(monkeypatch):
    monkeypatch.setenv("SUPABASE_DB_URL", "postgresql://x")
    monkeypatch.setenv("GOOGLE_API_KEY", "k")
    monkeypatch.setenv("TYPESAFE_API_KEY", "t")
    get_settings.cache_clear()
    s = get_settings()
    assert s.supabase_db_url == "postgresql://x"
    assert s.gemini_model == "gemini-2.5-flash"   # default
```
- [ ] **Step 2: Run to verify it fails** — `cd backend && pytest tests/test_config.py -v` → FAIL (module missing).
- [ ] **Step 3: Implement** `app/config.py` using `pydantic-settings` `BaseSettings` with the fields above and `@lru_cache` on `get_settings`. Add deps to `pyproject.toml`: `fastapi`, `uvicorn[standard]`, `pydantic`, `pydantic-settings`, `psycopg[binary]`, `langgraph`, `langchain-google-genai`, `typesafe-sdk`, `httpx`; dev: `pytest`, `pytest-asyncio`. Write `.env.example` listing `SUPABASE_DB_URL=`, `GOOGLE_API_KEY=`, `GEMINI_MODEL=gemini-2.5-flash`, `TYPESAFE_API_KEY=`.
- [ ] **Step 4: Run to verify it passes.**
- [ ] **Step 5: Commit** — `feat(backend): project scaffold and settings`.

### Task 1.2: Database schema

**Files:**
- Create: `db/schema.sql`
- Test: `backend/tests/test_schema.py`

**Interfaces:**
- Produces: 8 tables per §17 — `patient`, `dental_event`, `medical_condition`, `medication`, `allergy`, `clinical_note`, `investigation_run`, `agent_event` — **plus `imaging_study`** (`id` e.g. `IMG-001`, `patient_id`, `tooth_number`, `region_label` (authored ground truth), `image_url`, `source_label`, `recorded_at`, `metadata`) **and `conversation_transcript`** (`id` e.g. `CONV-001`, `patient_id`, `transcript_date`, `participants`, `transcript_text`, `summary`, `source_label`, `recorded_at`, `metadata`) — a searchable evidence source of prior visit conversations (user-approved). Every domain record table has a stable text `record_id`-compatible primary display id. Add a human `demo_identifier` on `patient` (e.g. `DEMO-007`) and a text `id` on record tables shaped as `MED-018`, `DENT-…`, `ALG-…`, `COND-…`, `NOTE-…`, `IMG-…` so evidence IDs match §12 examples.

- [ ] **Step 1: Write the failing test** — connect with `psycopg`, assert each of the 8 tables exists and required columns are present (§17 column lists).
- [ ] **Step 2: Run to verify it fails** (tables absent).
- [ ] **Step 3: Implement** `db/schema.sql` with the 8 tables. Use `text` ids for record tables (prefixed, human-readable) so `evidence_ids` are legible in the demo. `metadata jsonb`, `recorded_at timestamptz`. Apply via `psql "$SUPABASE_DB_URL" -f db/schema.sql`.
- [ ] **Step 4: Run to verify it passes.**
- [ ] **Step 5: Commit** — `feat(db): minimal schema (8 tables)`.

### Task 1.3: Synthetic seed data + scenario map

**Files:**
- Create: `db/seed.sql`, `db/scenarios.md`
- Test: `backend/tests/test_seed.py`

**Assigned to a dedicated build sub-agent (user instruction):** the `conversation_transcript` slice (table already in 1.2, its seed rows here, and the `search_conversations` tool in 1.6c) is implemented by a dedicated Claude sub-agent dispatched during Phase 1/2, reviewed at the gate like any other task.

**Interfaces:**
- Produces: exactly 12 patients incl. `DEMO-007` (the §7 warfarin/penicillin/AFib example). At least one patient each for **Scenario A (SURFACE)**, **B (DISMISS)**, **C (VERIFY)** (§8). **At least one patient has a `conversation_transcript` that contradicts a current record** — e.g. a prior visit where the patient reports stopping their anticoagulant while the medication row still reads "active" — driving a VERIFY (or SURFACE-for-review) via the transcript as evidence. **~3 synthetic radiographs** generated by `db/make_images.py` (Pillow) with authored `region_label` ground truth — one SURFACE-relevant, one DISMISS, one VERIFY-ambiguous — stored as PNG (repo `db/assets/imaging/` or Supabase Storage) and referenced by `imaging_study` rows. `scenarios.md` documents, per patient, the planned procedure, expected outcome, and which record (incl. imaging) proves it.

- [ ] **Step 1: Write the failing test** — assert `count(patient)==12`; assert `DEMO-007` has an active `medication` named `Warfarin` with a resolvable `id`; assert at least one patient has a clinical note mentioning a medication change with *no* corresponding current medication row (drives VERIFY, §8-C); assert at least one patient has a stale/contradicted candidate (drives DISMISS, §8-B).
- [ ] **Step 2: Run to verify it fails.**
- [ ] **Step 3: Implement** `db/seed.sql` (hand-authored, controlled). Encode DEMO-007 per §7. Author DISMISS and VERIFY fixtures deliberately. Write `db/scenarios.md`. Apply via `psql`.
- [ ] **Step 4: Run to verify it passes.**
- [ ] **Step 5: Commit** — `feat(db): 12 synthetic patients + scenario map`.

### Task 1.4: DB connection module

**Files:**
- Create: `backend/app/db.py`
- Test: `backend/tests/conftest.py` (fixture), `backend/tests/test_db.py`

**Interfaces:**
- Produces: `get_conn()` context manager yielding a `psycopg` connection using `Settings.supabase_db_url`. `conftest.py` provides a session-scoped `db` fixture.

- [ ] **Step 1: Write the failing test** — `test_db.py`: `with get_conn() as c: c.execute("select 1")` returns 1.
- [ ] **Step 2: Run to verify it fails.**
- [ ] **Step 3: Implement** `db.py` (thin `psycopg.connect` wrapper, dict rows). `# ponytail: single direct connection, add pooling only if concurrency demands it`.
- [ ] **Step 4: Run to verify it passes.**
- [ ] **Step 5: Commit** — `feat(backend): db connection`.

### Task 1.5: Record model + `get_record` (the evidence primitive)

**Files:**
- Create: `backend/app/models.py`, `backend/app/tools/records.py`, `backend/app/tools/__init__.py`
- Test: `backend/tests/test_tools.py`

**Interfaces:**
- Produces: pydantic `Record` = `{record_id: str, record_type: str, patient_id: str, source_label: str, recorded_at: datetime, data: dict}` (§11). `get_record(record_type: str, record_id: str) -> Record | None`.

- [ ] **Step 1: Write the failing test** — `get_record("medication", "MED-018")` for DEMO-007 returns a `Record` with matching `record_id` and `data["medication_name"]=="Warfarin"`; unknown id returns `None`.
- [ ] **Step 2: Run to verify it fails.**
- [ ] **Step 3: Implement** `Record` and `get_record` (maps `record_type` → table, selects by id, wraps row into `Record`).
- [ ] **Step 4: Run to verify it passes.**
- [ ] **Step 5: Commit** — `feat(tools): Record model + get_record`.

### Task 1.6: The seven investigation tools

**Files:**
- Modify: `backend/app/tools/records.py`
- Test: `backend/tests/test_tools.py`

**Interfaces:**
- Produces (all return `list[Record]` unless noted, all filter by `patient_id`):
  - `get_patient_summary(patient_id) -> Record` (patient row as a Record)
  - `get_dental_history(patient_id, tooth_number=None, event_types=None)`
  - `get_active_medications(patient_id)`
  - `get_medication_history(patient_id, medication_name=None)`
  - `get_allergies(patient_id)`
  - `get_medical_conditions(patient_id, status=None)`
  - `search_clinical_notes(patient_id, query, from_date=None, to_date=None)`

- [ ] **Step 1: Write the failing tests** — one per tool against seeded DEMO-007 (e.g. `get_active_medications` includes Warfarin; `get_dental_history(tooth_number=30)` returns the root canal + crown events; `search_clinical_notes(query="medication change")` returns the VERIFY-driving note).
- [ ] **Step 2: Run to verify they fail.**
- [ ] **Step 3: Implement** the seven functions in `records.py`. Parameterized SQL only. `# ponytail: naive ILIKE for note search, swap for FTS if recall matters`.
- [ ] **Step 4: Run to verify they pass.**
- [ ] **Step 5: Commit** — `feat(tools): seven deterministic record tools`.

### Task 1.6b: `get_imaging` (deterministic imaging tool)

**Files:**
- Create: `backend/app/tools/imaging.py`
- Test: `backend/tests/test_tools.py`

**Interfaces:**
- Produces: `get_imaging(patient_id, tooth_number=None) -> list[Record]` (imaging rows as `Record`s; `data` includes `image_url` and authored `region_label`). Note: the vision `read_imaging` lands in Phase 2 (needs the model); `get_imaging` is pure SQL and belongs to Gate 1.

- [ ] **Step 1: Write the failing test** — `get_imaging(DEMO-007, tooth_number=30)` returns the `IMG-…` record for the #30 region.
- [ ] **Step 2: Run to verify it fails.**
- [ ] **Step 3: Implement** `get_imaging` in `imaging.py` (parameterized select from `imaging_study`).
- [ ] **Step 4: Run to verify it passes.**
- [ ] **Step 5: Commit** — `feat(tools): get_imaging deterministic tool`.

### Task 1.6c: `search_conversations` (deterministic transcript tool) — dedicated build sub-agent

**Files:**
- Create: `backend/app/tools/conversations.py`
- Test: `backend/tests/test_tools.py`

**Interfaces:**
- Produces: `search_conversations(patient_id, query, from_date=None, to_date=None) -> list[Record]` (transcript rows as `Record`s; `data` includes `transcript_text` + `summary`). Owned by the Guardian (a tool, not a new agent).

- [ ] **Step 1: Write the failing test** — `search_conversations(<patient>, query="blood thinner")` returns the `CONV-…` record whose transcript reports stopping the anticoagulant.
- [ ] **Step 2: Run to verify it fails.**
- [ ] **Step 3: Implement** `search_conversations` (parameterized ILIKE over `transcript_text`/`summary`). `# ponytail: ILIKE, swap for FTS if recall matters`.
- [ ] **Step 4: Run to verify it passes.**
- [ ] **Step 5: Commit** — `feat(tools): search_conversations transcript evidence tool`.

### Task 1.7: GATE 1 verification test

**Files:**
- Create: `backend/tests/test_gate1.py`

- [ ] **Step 1: Write the test** — for every record id referenced in `db/scenarios.md`, assert `get_record(type, id)` returns a non-null `Record` whose `patient_id` matches. This is Gate 1: "the tool layer can retrieve every expected source record by ID."
- [ ] **Step 2: Run** — `cd backend && pytest tests/test_gate1.py -v` → PASS.
- [ ] **Step 3: Commit** — `test: Gate 1 — all scenario evidence retrievable by id`.

> **GATE 1 REVIEW (pause point):** run `database-reviewer` agent on `db/schema.sql` + `records.py`; run full `pytest`. Report to user. Do not start Phase 2 until user approves.

---

# PHASE 2 — AGENT CORE (roadmap; expand to bite-sized tasks at Gate 1 approval)

**Deliverable:** FastAPI service + LangGraph graph running the four agents against the tools, producing SURFACE/DISMISS/VERIFY with evidence IDs from the terminal/API.

**Tasks:**
- 2.1 `provider.py` — Gemini adapter (`langchain-google-genai` `ChatGoogleGenerativeAI` with `gemini_model`, `GOOGLE_API_KEY` server-side) — a single vision+tool-calling client used by the Guardian **and** `read_imaging`. Plus `jev.py` — TypeSafe client wrapper (`typesafe-sdk`, reads `TYPESAFE_API_KEY`) exposing `choice(state, instructions, criteria)` and `noul(state, instructions)` helpers. Includes a one-shot reliability probe (§25 step 11) for both providers.
- 2.2 `models.py` — `InvestigationState` (§13), `Candidate`, `SkepticResult`, `Card`, `AgentEvent`.
- 2.3 `tools/__init__.py` — tool JSON schemas + registry binding the Phase-1 functions (incl. `get_imaging`) for tool-calling (§11). `read_imaging(record_id)` added in `tools/imaging.py`: sends the image to the Gemini vision model for locate+relevance, then **validates the reported region against `region_label`**; disagreement/uncertainty flags the candidate uncertain (→ Skeptic VERIFY/DISMISS). Never returns a diagnosis.
- 2.3b `playbook.py` — static authored `procedure_playbook: dict[str, list[str]]` mapping procedure → record categories commonly worth investigating (pattern-informed steering, Reading A). Pure data + a `hint_tools_for(procedure) -> list[str]` helper. No advice, no treatment logic. `# ponytail: static dict, not an ML model`.
- 2.4 `agents/context_interpreter.py` (§9.1) — normalize intent, preserve ids, flag missing context, never invent facts.
- 2.5 `agents/guardian.py` (§9.2) — model-driven tool selection loop; **consults `playbook.hint_tools_for(procedure)` as a starting hint** but remains free to deviate/follow discoveries (preserves §10 agency — the hint is not a fixed order); chooses next tool from observations; emits candidates. May call imaging tools when the procedure/tooth warrants, and `search_conversations` to check prior-visit transcripts for contradictions.
- 2.6 `agents/skeptic.py` (§9.3) — **runs on Jev**: 8 Noul checks (this-patient? source real? relevant? current? contradicted? duplicate? card overclaims? UI-linkable?) over the candidate + its `Record`s, then a Choice → SURFACE/DISMISS/VERIFY. No confidence %; enforces the evidence contract (drops any candidate lacking a resolvable `evidence_id`). `.env.example` gains `TYPESAFE_API_KEY`.
- 2.7 `agents/composer.py` (§9.4) — approved evidence → card copy using **safe language only** (Global Constraints). `reason_shown` may cite the *pattern* behind surfacing ("medications are commonly relevant to extractions") but never an instruction. Imaging cards read "imaging record to review — <region>", never a finding.
- 2.8 `graph.py` — assemble LangGraph: interpreter → guardian ↔ tools → skeptic → composer; persists trace via `trace.py`.
- 2.9 `main.py` — routes (§16): `/health`, `/demo/patients`, `/patients/{id}`, `POST /investigations`, `GET /investigations/{id}`, `GET /investigations/{id}/trace`, `GET /evidence/{type}/{id}`, `POST /demo/reset`.

**Gate 2 (§25):** From terminal/API, Scenario A→SURFACE, B→DISMISS, C→VERIFY, and every factual result carries evidence IDs.

> **GATE 2 REVIEW:** `fastapi-reviewer`, `python-reviewer`, `rag-pipeline-reviewer`, `security-reviewer` (key never client-side), `healthcare-reviewer` (safe language). Pause for user.

---

# PHASE 3 — PROVE REAL AGENCY (roadmap)

**Deliverable:** evidence that the agent is not a fixed pipeline (§10).

**Tasks:** record tool calls per run; assert different scenarios produce different tool-call sequences; assert a finding can trigger a follow-up tool call; assert the model can choose to stop; assert it does not always call every tool.

**Gate 3 (§25):** two demo patients visibly produce different investigation paths. **Essential for the Agents track.**

> **GATE 3 REVIEW:** `agent-evaluator`; `test_agency.py` green. Pause for user.

---

# PHASE 4 — UI (roadmap)

**Deliverable:** the 5 screens (§20), mobile-first, working end-to-end from a phone/browser.

**Tasks:** Next.js scaffold + Tailwind; `lib/api.ts` typed client; Screen 1 patient selector; Screen 2 procedure/tooth form; Screen 3 investigation + **judge-visible Agent Trace** (lightweight polling of `/trace`, §15) — trace shows imaging-tool calls too; Screen 4 result cards; Screen 5 evidence drawer that **renders the synthetic image via `<img>`** (no DICOM viewer, §28 stays future) under the `SYNTHETIC DATA — PROTOTYPE` banner; demo reset. Direction: calm/clinical/trustworthy (`minimalist-ui` + `design-taste-frontend`); trace uses restrained motion (`motion-ui`); a11y throughout (`accessibility`).

**Gate 4 (§25):** complete flow works from phone/browser without terminal.

> **GATE 4 REVIEW:** `react-reviewer`, `typescript-reviewer`, `a11y-architect`; `e2e-runner` smoke. Pause for user.

---

# PHASE 5 — RELIABILITY (roadmap)

**Deliverable:** repeatable demo.

**Tasks:** run Scenario A/B/C ×5 each; assert no unsupported record ever appears (evidence contract); assert every card opens its evidence; assert errors fail safely per §22 table.

**Gate 5 (§25):** five consecutive full demo runs succeed.

> **GATE 5 REVIEW:** `silent-failure-hunter` against §22; `pr-test-analyzer`. Pause for user.

---

# PHASE 6 — SUBMISSION (roadmap)

**Deliverable:** deployed app + public repo + README + demo.

**Tasks:** deploy frontend/backend (`vercel:deploy` for frontend; backend host TBD at gate); public repo; quick-start README (`code-tour`); architecture diagram; `.env.example`; document synthetic-data provenance + limitations; record 2–5 min demo; write-up; submit. Final `security-reviewer` + `opensource-sanitizer` secret scan before publishing.

**Definition of Done:** §27 checklist.

---

## Self-Review

**Spec coverage (§ → task):** §7 data→1.3; §8 scenarios→1.3/2.x; §9.1–9.4 agents→2.4–2.7; §10 agency→Phase 3; §11 tools→1.5/1.6/1.6b/2.3; §12 evidence contract→Global Constraints + 1.5/2.6; §13 state→2.2; §14 stack→scaffold; §16 API→2.9; §17 schema→1.2; §20 UI→Phase 4; §21 safe language→Global Constraints + 2.7 + healthcare-reviewer; §22 failure→Phase 5; §25 gates→each phase; §27 DoD→Phase 6. **User-approved additions:** vision/imaging→1.2/1.3/1.6b/2.3 (+ Global Constraints fail-safe gate); pattern-informed investigation (Reading A)→2.3b/2.5 (+ Global Constraints steering-not-advice rule); conversation-transcript evidence source→1.2/1.3/1.6c/2.5 (Guardian tool; dedicated build sub-agent). **No uncovered sections.**

**Placeholder scan:** Phase 1 is fully step-level. Phases 2–6 are intentionally task-level roadmaps expanded at each gate per the chosen cadence — flagged explicitly, not hidden TODOs.

**Type consistency:** `Record` shape fixed in 1.5 and reused by all tools (1.6), the registry (2.3), and `get_record` evidence lookups; `evidence_ids: list[str]` of `record_id`s threads Candidate→SkepticResult→Card unchanged.
