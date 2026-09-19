# Investigation run: trace, cards, silence

The core loop. The UI polls `GET /investigations/{run_id}` for status and `GET /investigations/{run_id}/trace` for live steps. Guardian (Gemini, ReAct over record tools) proposes candidate evidence, Skeptic (TypeSafe Jev) decides SURFACE / DISMISS / VERIFY per candidate, Composer turns survivors into cards. A run with no survivors lands on the informative silence screen.

## Sub-features
- Animated trace: `context_interpreter context` → `guardian tool_call` × N → `guardian candidates` → `skeptic challenge` → `skeptic decision` × N → `composer cards`
- Result cards titled `Record to review — …` (SURFACE) and `Item to verify — …` (VERIFY), each with `evidence_ids` and `reason_shown`
- Silence screen when nothing survives the Skeptic
- Investigation summary and recap view
- Safe failure: on provider error the trace ends with `system error "Investigation failed safely; no unsupported result shown"` and status is `error`

## How to get to it (user POV)
Pick a patient, choose a procedure, submit. Wait 10–30 s.

## Driving it with verify.sh / agent-browser
- API: `verify.sh drive DEMO-007 extraction 30`. Passes when status is `complete`, the trace has guardian tool calls, skeptic decisions, and composer cards, and `final_cards` is non-empty. Reference run 2026-09-19: 19 trace steps, 9 tool calls, 6 candidates, 4 cards (Warfarin, Penicillin allergy, atrial fibrillation as SURFACE; a medication-change note as VERIFY), 2 dismissed, 17 s.
- UI: after submit, `agent-browser wait --text "Record to review" --timeout 90000`, then `agent-browser screenshot`. For a silence case pick a thin patient and `cleaning`, and wait for the silence screen text instead.

## Gotchas
- `status: error` with `API key not valid` while `doctor` says the key is valid means the backend was started with a stale `GOOGLE_API_KEY` in the process environment. Relaunch with the helper.
- Runs are stored in Supabase; `POST /demo/reset` deletes them. Never call it during a proof.
- Gemini latency varies; the helper allows 180 s before failing.
