# Agentic Loupes — Build Plan

AI assistant for dentists. Sees what the dentist sees through their loupes, hears the room, answers on a wake word with patient-specific context, and remembers what it found.

**Demo promise:** dentist says *"Hey Loupes, what's the history on this tooth?"* → identifies the tooth by number from the camera, pulls that tooth's record, answers out loud in under 3 seconds, circles it on screen — **and writes the finding back so it knows it later.**

**Deadline: Sept 19, 7:00 PM CST.** Submit via the Airtable form. Late = zero.

---

## 1. The line that changes our design

> *"Submissions that could have been entered in any track without changing a line of code will score low here."* — Track Fit, 20 pts

> *"Build an AI agent capable of independent, meaningful action... real memory, tool use, and reasoning about what to do next, **not an LLM API wrapper with a chat window**."* — Agents Track

Our previous design — one Live session calling three stateless tools — is clean engineering but it is, structurally, a wrapper with a voice. It scores well on Technical Execution and poorly on Track Fit.

**Fix: make the memory real and add one autonomous behavior.** Supabase gives us the first. The second is ~30 minutes of work and it's the highest-scoring thing we can build today.

### The autonomous loop — this is our Track Fit answer

After every exchange, without being asked, the system:
1. Writes a structured finding to `session_findings` (tooth, observation, source, confidence, timestamp)
2. Compares it against that tooth's prior history
3. **Raises a flag unprompted** if something diverges — pocket depth worsening, a restoration aging past expected life, a symptom matching a case pattern

Then later in the demo, unprompted, the agent says:

> *"Before you numb — you flagged sensitivity on 19 two minutes ago, and its pocket depth has gone 3mm to 4mm since March. Also, penicillin allergy on file."*

That sentence is worth more points than any other feature on this list. Memory, autonomous reasoning, and non-obvious insight in one breath. **Do not cut it.**

---

## 2. Track choice — pick ONE, in the next ten minutes

| | Agents Track | Most Commercializable |
|---|---|---|
| Our fit | Strong, *if* the §1 loop ships | Strong — real dentist on the team, named buyer |
| What it needs | Memory, tool use, autonomous action | Defined customer, revenue model, **"the buying moment" on camera** |
| Extra work | The §1 autonomous loop | Pricing slide + the insurance-data wedge |

**Recommendation: Agents Track.** The autonomous loop is the more defensible build and our architecture already points there. If the team would rather compete on the business case, decide now — it changes the demo script, not the code.

Either way, **name the track explicitly in the write-up and in the first 15 seconds of the video**, and use that track's vocabulary. Judges score against a rubric.

### Scoring map — what we're deliberately buying

| Criterion | Pts | Our play |
|---|---|---|
| Completeness | 15 | Runs **live**, not recorded. Rehearse twice. Graceful failure on every path. |
| Technical Depth | 15 | Realtime multimodal pipeline + pretrained CV + persistent agent memory. Not one API call. |
| Track Fit | 20 | §1 autonomous loop. Say "memory, tool use, autonomous action" out loud. |
| Insight Quality | 13 | The unprompted divergence flag. Non-obvious by construction. |
| Usability | 12 | Wake word + voice = zero learning curve. Nobody reads a manual. |
| Creativity | 13 | Loupes form factor + open medical model + realtime dental CV. Nobody else is doing dentistry. |
| Performance | 12 | Sub-3s response. Show it handling a **miss**. |

**On Performance — demo one failure deliberately.** Point at a tooth the model can't read and let the agent say *"I can't get a clear read on that one, give me the number?"* Judges score recovery, not perfection, and a clinical system that admits uncertainty is the correct design anyway.

---

## 3. Decisions — do not relitigate

| Question | Decision |
|---|---|
| Framework | **Split.** Realtime path = plain async Python + Gemini Live. Reasoning path = LangGraph. See §3.1 — the split is not optional. |
| Platform | Web (React). Not native. Runs in phone browser. |
| DB | **Supabase** (Postgres). Patient records, session memory, case corpus. |
| Retrieval | Postgres queries keyed by tooth number. pgvector only if ahead of schedule. |
| Trigger | Wake phrase `"hey loupes"`. Never speaks unprompted **except** the §1 flag. |
| Tooth detection | Pretrained Roboflow dental YOLO. **We train nothing.** |
| Segmentation | Cut. Bounding boxes only. No SAM 2. |
| Demo footage | Pre-recorded cleaning video on a second screen. **We do not film a real mouth.** |

### 3.1 Where LangChain / LangGraph goes — and where it cannot

**It cannot own the realtime path.** Gemini Live is a persistent bidirectional WebSocket streaming PCM audio in and out with server-side VAD. LangChain has no abstraction for that — its model interfaces are request/response. There is no adapter to reach for. If you try to route the voice loop through LangChain you will spend three hours discovering this. `live_session.py` stays raw `websockets`.

**It should own the reasoning path.** `reconcile.py` is genuinely a graph: read findings → compare to history → branch on divergence type → decide whether to interrupt. That's what LangGraph is for, and it's the one place a framework earns its weight today.

Use **LangGraph**, not classic LangChain chains. Chains are the wrong abstraction and the deprecated half of the library.

```python
# MedGemma on Featherless is OpenAI-compatible — one line, no custom class
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="google/medgemma-27b-text-it",
    base_url="https://api.featherless.ai/v1",
    api_key=os.environ["FEATHERLESS_API_KEY"],
)
```

**Bonus if it works out:** LangGraph's Postgres checkpointer points at a Supabase connection string. That gives you graph state persisted in the same DB as `session_findings` — literally "shared memory state" in the Track Fit language, for free. Nice to have, not load-bearing.

**Time box: 45 minutes.** If `reconcile.py` isn't running in LangGraph by T+2:00, rip it out and write 40 lines of plain Python. The divergence logic is four `if` statements — the framework is scaffolding around it, not the thing itself. Learning happens on the branch that can be abandoned without killing the demo.

### Why not MedGemma for vision
MedGemma and MedSigLIP are trained on chest X-rays, dermatology, ophthalmology, histopathology. **No dental imaging in the training distribution.** It answers confidently and wrongly about teeth. We use it as the *text reasoning* model only — and we say so in the write-up, because knowing that is itself a signal of depth.

---

## 4. Architecture

```
┌──────────────────────── BROWSER (phone or laptop) ────────────────────────┐
│  getUserMedia ──┬──► <video> ──► canvas overlay (boxes, circle, flag)     │
│                 ├──► frame grab @ 1–2 FPS ──► JPEG b64 ──┐                │
│                 └──► mic PCM 16kHz ──────────────────────┤                │
│  transcript ◄── text deltas ─────────────────────────────┤                │
│  audio out  ◄── PCM ─────────────────────────────────────┤                │
└──────────────────────────────────────────────────────────┼────────────────┘
                                                           │ our WebSocket
┌──────────────────────── BACKEND (FastAPI) ────────────────▼───────────────┐
│  ws_relay ──► wake_word gate ──► Gemini Live session (persistent WSS)      │
│                                        │ function_call                    │
│         ┌──────────────────────────────▼──────────────────────────┐       │
│         │ TOOLS                                                   │       │
│         │  detect_teeth(frame)          ──► Roboflow YOLO         │       │
│         │  get_tooth_record(n)          ──► Supabase              │       │
│         │  find_similar_cases(finding)  ──► Supabase + MedGemma   │       │
│         │  log_finding(n, obs)          ──► Supabase  [autonomous]│       │
│         └──────────────────────────────┬──────────────────────────┘       │
│                                        │                                  │
│  reconcile_agent ◄─── after every turn ┘                                  │
│    reads session_findings + tooth history → diverged? → push flag         │
└────────────────────────────────────────┬──────────────────────────────────┘
                                         ▼
                              ┌──────────────────────┐
                              │ SUPABASE (Postgres)  │
                              │  patients            │
                              │  teeth               │
                              │  session_findings ★  │ ← the memory
                              │  cases               │
                              └──────────────────────┘
```

★ `session_findings` is what makes this an agent instead of a chatbot. It persists across turns and across sessions.

**Model assignment**

| Layer | Model | Notes |
|---|---|---|
| Realtime voice + video | `gemini-2.5-flash-native-audio-preview-12-2025` | Only option with bidi audio. STT, TTS, orchestration, tool calls. |
| Tooth detection + FDI numbering | `teeth-detection-and-numbering-agi2i/18` (Roboflow) | Hosted API. Browser `inferencejs` if latency is bad. |
| X-ray pathology (optional) | `liodon-ai/dental-panoramic-detector` | Caries recall is weak — present as screening hint, not diagnosis. |
| Clinical reasoning + reconcile | `google/medgemma-27b-text-it` via Featherless | Our $25. Low volume. **Warm it before every run.** |

---

## 5. Supabase schema

Run in the SQL editor. Two minutes.

```sql
create table patients (
  id text primary key,
  name text,
  bp text,
  allergies text[],
  vitals_taken_at timestamptz
);

create table teeth (
  patient_id text references patients(id),
  tooth text,                        -- must match Roboflow class labels EXACTLY
  restoration text,
  periodontal_depth_mm int,
  last_treated date,
  notes text,
  xray_url text,
  primary key (patient_id, tooth)
);

-- ★ the memory. written autonomously, read on every turn.
create table session_findings (
  id bigserial primary key,
  session_id text,
  patient_id text,
  tooth text,
  observation text,
  source text,                       -- 'cv' | 'dentist_speech' | 'patient_speech'
  confidence real,
  created_at timestamptz default now()
);

create table cases (
  id text primary key,
  summary text,
  findings text,
  outcome text
);

alter table patients enable row level security;
alter table teeth enable row level security;
alter table session_findings enable row level security;
alter table cases enable row level security;
-- demo only: backend uses the service key, browser never touches these tables.
```

**Service role key stays on the backend.** Never ship it to the browser. Judges read repos.

---

## 6. Folder structure

```
agentic-loupes/
├── README.md                   ← GRADED. see §8. write at T+4:30, not T+5:55.
├── plan.md                     ← this file
├── .env.example
├── .gitignore
│
├── backend/                                            [OWNER: A]
│   ├── main.py                 # FastAPI app, /ws endpoint
│   ├── live_session.py         # Gemini Live WSS session manager
│   ├── wake_word.py            # regex gate on transcript
│   ├── reconcile.py            # ★ autonomous divergence check (§1)
│   ├── schemas.py              # SHARED CONTRACT, see §7
│   ├── tools/
│   │   ├── __init__.py         # TOOL_DECLARATIONS for Live config
│   │   ├── detect_teeth.py     [A]
│   │   ├── tooth_record.py     [B]
│   │   ├── similar_cases.py    [B]
│   │   └── log_finding.py      [B]
│   ├── clients/
│   │   ├── roboflow.py
│   │   ├── featherless.py
│   │   └── supabase.py
│   └── requirements.txt
│
├── db/                                                 [OWNER: B]
│   ├── schema.sql              # §5
│   ├── seed.sql                # one patient, 4 teeth, 15 cases
│   └── PROVENANCE.md           # GRADED. source of every image and row.
│
├── frontend/                                           [OWNER: C]
│   ├── index.html
│   ├── package.json
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── CameraFeed.jsx      # getUserMedia, frame grab loop
│       ├── Overlay.jsx         # canvas: boxes, highlight circle
│       ├── Transcript.jsx      # rolling text panel
│       ├── FlagBanner.jsx      # ★ the unprompted alert. make it look good.
│       ├── audio.js            # mic → PCM, playback
│       └── ws.js               # SHARED CONTRACT, see §7
│
├── demo/
│   ├── script.md               # word-for-word run
│   ├── writeup.md              # 150–300 words, GRADED
│   └── assets/
│
└── scripts/
    ├── warmup_featherless.py   # RUN BEFORE EVERY REHEARSAL
    └── smoke_test_roboflow.py
```

---

## 7. Contracts — freeze first, then parallelize

**Nobody writes feature code until this is agreed.** Once it exists, A/B/C never block each other.

### 7.1 Browser ↔ Backend WebSocket

Client → server:
```json
{"type": "audio", "data": "<base64 PCM16 16kHz mono>"}
{"type": "frame", "data": "<base64 JPEG>", "ts": 1758300000}
```

Server → client:
```json
{"type": "transcript", "role": "user", "text": "...", "final": true}
{"type": "audio", "data": "<base64 PCM16 24kHz>"}
{"type": "overlay", "boxes": [
    {"tooth": "FDI_19", "x": 0.41, "y": 0.52, "w": 0.08, "h": 0.11,
     "conf": 0.94, "highlight": true, "label": "19 — composite 2024"}]}
{"type": "flag", "tooth": "FDI_19", "severity": "watch",
 "message": "Pocket depth 3mm → 4mm since March", "basis": ["finding:12", "history"]}
{"type": "status", "state": "idle"}
```

Box coords **normalized 0–1**, origin top-left. C scales to canvas and never needs the camera resolution.

`flag` is pushed by the server **unprompted** — C must handle it arriving at any time, not only after a query.

### 7.2 Tool signatures

```python
def detect_teeth(frame_b64: str) -> dict:
    """-> {"boxes": [Box, ...]}"""

def get_tooth_record(tooth: str, patient_id: str) -> dict:
    """-> teeth row + recent session_findings for that tooth"""

def find_similar_cases(findings: str) -> dict:
    """-> {"cases": [...], "reasoning": str}"""

def log_finding(tooth: str, observation: str, source: str, confidence: float) -> dict:
    """-> {"id": int}   ← called autonomously, not on user request"""
```

All sync, all return JSON-serializable dicts. A stubs them in minute one with hardcoded returns and is never blocked on B.

---

## 8. README — graded, treat as a deliverable

Required sections, verbatim from the rules:

- [ ] **Quick start** — exact copy-pasteable commands
- [ ] **Tech stack & architecture diagram** — paste §4's ASCII, simple is fine
- [ ] **How to reproduce the demo** — env vars, API keys, sample `.env`
- [ ] **Datasets / synthetic data + provenance** — link `db/PROVENANCE.md`. State clearly that patient data is **synthetic and contains no PHI**. This matters in a health demo.
- [ ] **Known limitations & next steps** — specific and honest: Roboflow model trained on ~1.4k images; MedGemma not dental-trained; no de-identifying gateway yet; not a diagnostic device. This section *gains* points. Vagueness loses them.

Repo must be **publicly viewable**. Verify in an incognito window before submitting.

---

## 9. Timeline — work backwards from 7:00 PM

**The submission block is not negotiable. Everything else compresses into what's left.**

| Time | Block |
|---|---|
| **T+0:00 → 0:30** | Contracts + smoke tests. Everyone together. |
| **0:30 → 3:00** | Three parallel tracks |
| **3:00 → 4:30** | Integration. Autonomous loop wired. |
| **4:30** | **HARD CODE FREEZE.** No new features after this. For any reason. |
| **4:30 → 5:30** | README, write-up, PROVENANCE, rehearse live twice |
| **5:30 → 6:15** | Record Loom video (2–5 min). Budget 3 takes. |
| **6:15 → 6:45** | Airtable submission. Every field. Confirm repo is public. |
| **6:45 → 7:00** | Buffer. You will need it. |

### T+0:00 → 0:30, everyone together
- Agree §7 contracts. Commit `schemas.py` and `ws.js` with types only.
- Create Supabase project, run `schema.sql`, share keys in the team channel.
- **A: smoke-test Roboflow against a real frame from the demo video.** If numbering fails → fall back to generic detection + dentist speaks the number. Decide now, not at hour four.
- **B: run `warmup_featherless.py`.** Confirm `google/medgemma-27b-text-it` resolves; time the cold start.
- **C: get HTTPS working** (`vite --host` + ngrok). `getUserMedia` is blocked on plain HTTP from a non-localhost origin. This kills more demos than any model problem.

### 0:30 → 3:00, parallel

**A — realtime backend** *(strongest engineer, critical path)*
Gemini Live WSS session · wake-word gate (system instruction **and** client-side regex — both; the instruction alone leaks) · register 4 tools · `detect_teeth` wired to Roboflow

**B — data, tools, autonomous loop**
`seed.sql` (one patient, 4 teeth fully populated — nobody looks at 32) · 15 cases · `get_tooth_record`, `log_finding`, `find_similar_cases` · **`reconcile.py`, the §1 divergence check** · `PROVENANCE.md`
*At T+2:00 B moves to help A. Data is done or it's good enough.*

**C — frontend**
Camera + mic + WS · canvas overlay · transcript · **`FlagBanner` — make the unprompted alert look genuinely good, it's the money shot** · mock the WS locally, never wait on A

---

## 10. Cut list

Behind at T+3:00, cut in this order:

1. `find_similar_cases`
2. X-ray pathology detection
3. Patient-facing second screen
4. Audio output → fall back to text on screen

**Never cut:** wake word · tooth detection + numbering · `get_tooth_record` · **the §1 autonomous flag.** Those four *are* the submission.

---

## 11. Demo script skeleton

1. Point phone at cleaning video on second screen
2. Boxes appear with tooth numbers — **hold 3 seconds before speaking, let it land**
3. *"Hey Loupes, what's the history on nineteen?"* → composite 2024, 3mm pocket, watch distal margin. Circle animates on.
4. *"Patient says it's sensitive to cold."* → agent logs it silently. **Point this out:** "notice it wrote that down without being asked."
5. Point at an unreadable tooth → agent asks for the number. **Say: "it knows when it doesn't know."**
6. *"Hey Loupes, ready to numb."* → **unprompted flag fires**: sensitivity logged two minutes ago + depth worsening since March + penicillin allergy
7. Close on deployment: data stays in the practice, open medical model runs locally, de-identifying gateway in front of any external call

Say once, out loud: *proof of concept, not a diagnostic device.* Four seconds, buys credibility.

### Demo video (2–5 min, Loom)
Show the **core loop live**. Structure: 20s problem → 30s what it is → **2.5 min live run** → 30s architecture and next steps. Do not spend a minute on slides. Name the track in the first fifteen seconds.

---

## 12. Setup

```bash
git clone <repo> && cd agentic-loupes
cp .env.example .env

cd backend && pip install -r requirements.txt && uvicorn main:app --reload
cd frontend && npm install && npm run dev -- --host
```

`.env.example`:
```
GEMINI_API_KEY=
ROBOFLOW_API_KEY=
FEATHERLESS_API_KEY=
SUPABASE_URL=
SUPABASE_SERVICE_KEY=        # backend only, never ship to browser
PATIENT_ID=P-88204
SESSION_ID=demo-1
WAKE_PHRASE=hey loupes
```

---

## 13. Risks

| Risk | Mitigation |
|---|---|
| Roboflow numbering fails on our footage | Test at T+0:15. Fall back to generic detection + spoken number. |
| Featherless cold start | Warm before every rehearsal and before recording. |
| Agent talks at the wrong moment | Double wake-word gate. The §1 flag is the *only* sanctioned interruption. |
| Audio format mismatch eats 2 hours | Budgeted into the 3:00–4:30 block. |
| Phone can't focus at mouth distance | Solved: we film a screen. |
| **Submission rushed, fields missed** | The 6:15 block is reserved. Freeze at 4:30 and mean it. |

---

## 14. Team roster — fill in now, it's a required field

| Name | Role | Contact |
|---|---|---|
| | Backend / realtime (A) | |
| | Data / agents (B) | |
| | Frontend (C) | |
| | Domain (dentistry) | |
