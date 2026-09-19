# Scenario sweep — every demo patient through the real agent

Run against head `7ac2efc` on 2026-09-19, 17:23–17:31 CDT, by the verify-dentassist
harness (`.claude/skills/verify-dentassist/scripts/verify.sh drive`). Every row is a real
`POST /investigations` against the live Supabase and Gemini, polled to completion, with the
trace and cards saved. Evidence paths are relative to `.verify/evidence/`.

All twelve patients completed. No run errored.

Intended procedure and tooth come from `db/scenarios.md` and the scenario pre-fill in
`frontend/components/PatientSelect.tsx`. Three patients (DEMO-013, DEMO-015, DEMO-018) have
no authored suggestion; the procedure there was chosen to match the tooth in their own seeded
records, and is marked below.

## The table

SURFACE and VERIFY count the cards the dentist sees. DISMISS is `dismissed_count` — candidates
the Skeptic rejected, which never become cards. "Silence" means the run ended with zero cards
and the review-complete screen instead of results.

| Patient | Procedure | Tooth | Status | Secs | SURFACE | VERIFY | DISMISS | Silence | Evidence |
|---|---|---|---|---|---|---|---|---|---|
| DEMO-007 | extraction | 30 | complete | 18 | 3 | 3 | 3 | no | `20260919-172321/` |
| DEMO-008 | extraction | 3 | complete | 7 | 0 | 0 | 0 | **yes** | `20260919-172643/` |
| DEMO-009 | extraction | 19 | complete | 10 | 1 | 1 | 0 | no | `20260919-172712/` |
| DEMO-010 | extraction | 30 | complete | 10 | 1 | 0 | 0 | no | `20260919-172726/` |
| DEMO-011 | implant | 8 | complete | 10 | 2 | 0 | 0 | no | `20260919-172739/` |
| DEMO-012 | root_canal | 9 | complete | 9 | 2 | 0 | 0 | no | `20260919-172753/` |
| DEMO-013 | cleaning | 8 † | complete | 9 | 1 | 1 | 0 | no | `20260919-172803/` |
| DEMO-014 | filling | 12 | complete | 10 | 3 | 0 | 0 | no | `20260919-172824/` |
| DEMO-015 | extraction | 19 † | complete | 10 | 1 | 0 | 1 | no | `20260919-172838/` |
| DEMO-016 | extraction | 14 | complete | 11 | 3 | 1 | 0 | no | `20260919-172851/` |
| DEMO-017 | crown | 30 | complete | 26 | 1 | 0 | 0 | no | `20260919-172904/` |
| DEMO-018 | implant | 3 † | complete | 6 | 0 | 0 | 0 | **yes** | `20260919-172934/` |

† procedure chosen by the sweep — no authored suggestion for this patient.

Two extra confirmation runs, taken because the first result contradicted the authored scenario:

| Patient | Procedure | Tooth | Status | Secs | SURFACE | VERIFY | DISMISS | Silence | Evidence |
|---|---|---|---|---|---|---|---|---|---|
| DEMO-008 | extraction | 3 | complete | 7 | 0 | 0 | 0 | **yes** | `20260919-173059/` |
| DEMO-010 | extraction | 30 | complete | 11 | 1 | 0 | 1 | no | `20260919-173108/` |

## Determinism pair — DEMO-007, extraction #30

Two identical runs, back to back. **They do not match.**

| | Run 1 `20260919-172321/` | Run 2 `20260919-172953/` |
|---|---|---|
| Seconds | 18 | 12 |
| Candidates proposed | 9 | 5 |
| Cards | 6 | 4 |
| SURFACE / VERIFY / DISMISS | 3 / 3 / 3 | 2 / 2 / 1 |

Cards present in run 1 and missing from run 2:

- `SURFACE — Record to review — Visit Conversation Transcript` (`CONV-007`)
- `VERIFY — Item to verify — Clinical Note: Medication change` (`NOTE-007`)

The transcript card is the one `db/scenarios.md` calls the key demo case: the patient says they
stopped Warfarin, the chart still lists it active. It is a coin flip whether it is on screen.
Filed as #32.

Stable across both runs: the Warfarin VERIFY (`MED-018`), the Penicillin SURFACE (`ALG-007`),
the atrial-fibrillation SURFACE (`COND-007A`), and the stray uploaded-imaging VERIFY.

## Where the run contradicted the plan

| Expected (`db/scenarios.md` / `PLAN.md` §8) | Observed | Issue |
|---|---|---|
| DEMO-008 → DISMISS: `MED-008` and `COND-008` dismissed after verification | Guardian proposes 0 candidates after 11 tool calls; Skeptic never runs; silence with `dismissed=0`. Same in both runs. | [#31](https://github.com/agenticLoupes/agenticloop/issues/31) |
| DEMO-007 → the `CONV-007` transcript contradiction, every time | Present in run 1, absent in run 2 | [#32](https://github.com/agenticLoupes/agenticloop/issues/32) |
| DEMO-010 → `IMG-001` SURFACE **and** `IMG-002` DISMISS | Run 1 surfaced only, dismissed 0; run 2 did both | [#33](https://github.com/agenticLoupes/agenticloop/issues/33) |
| Demo patients carry only their seeded records | Four leftover `IMG-UP-*` uploads on DEMO-007, 010, 013, 016 add an unplanned VERIFY card | [#34](https://github.com/agenticLoupes/agenticloop/issues/34) |

DEMO-018 lands on silence with zero candidates in the same shape as DEMO-008; it has no authored
expectation, so it is recorded inside #31 rather than as a contradiction of its own.

Also blocking before any of this could run: the backend could not start from a clean install
because `python-multipart` is undeclared — [#26](https://github.com/agenticLoupes/agenticloop/issues/26).

## Patients recommended for the video

**DEMO-014 — filling, tooth #12.** The most reliable positive. Three SURFACE cards in 10s, all
from seeded records with real evidence ids: a documented Lidocaine reaction, Type 2 diabetes, and
active Metformin. Nothing stray, nothing flaky.

**DEMO-009 — extraction, tooth #19.** The VERIFY moment, and the strongest idea in the product:
a note reports a blood-thinner change and there is no medication row to confirm it, so the agent
says the current status cannot be established instead of inventing certainty. It also surfaces the
#19 radiograph, so one patient shows both card types.

**DEMO-012 — root canal, tooth #9.** Clean, fast (9s), two SURFACE cards from a latex allergy and
the matching intake condition. Good as a short third example or a safe substitute.

On DEMO-007: it is the scripted hero and it does work, but its best card appears in roughly half
of runs (#32) and it carries a stray uploaded-image card that names a third, unrelated tooth (#34).
Clear those two and it is the right opener. Until then, rehearsing on it does not guarantee the
take.

On DEMO-008 as the silence demo: the screen renders correctly and reads as intended on camera, but
the dismissal count behind it is 0 — nothing was actually challenged (#31). Showing it as "the
agent chose to stay quiet" is honest; saying "candidates were dismissed after verification" is not.
