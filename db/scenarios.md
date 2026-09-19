# Synthetic demo scenarios (100% synthetic — no real patients)

Patient key = demo identifier. Procedure is entered at demo time (not stored). Expected
outcome is what the Guardian + Skeptic (Jev) should produce.

| Patient | Enter procedure | Expected | Proof (evidence ids) |
|---|---|---|---|
| **DEMO-007** | Extraction, tooth #30 | **SURFACE** | Active Warfarin `MED-018` + Penicillin allergy `ALG-007` — records to review before an extraction |
| **DEMO-008** | Extraction, tooth #3 | **DISMISS** | Only stale/unrelated candidates: discontinued `MED-008`, resolved `COND-008` — dismissed after verification |
| **DEMO-009** | Extraction, tooth #19 | **VERIFY** | Note `NOTE-009` reports a blood-thinner change but there is **no** current medication row → status cannot be established |
| **DEMO-010** | Extraction, tooth #30 | **SURFACE (imaging)** + **DISMISS (imaging)** | `IMG-001` (#30 region) is relevant → surface; `IMG-002` (#3 region) is irrelevant → dismiss |
| DEMO-011..018 | various | mixed | lighter records; used to show different tool paths (Gate 3) |

## Fail-safe note (imaging)
`imaging_study.region_label` is authored ground truth. `read_imaging` (Gemini, locate+relevance
only) is validated against it: agreement + relevance → eligible to SURFACE; disagreement/uncertainty
→ VERIFY/DISMISS. A vision hallucination can never produce a false SURFACE.

## Transcript scenario (Task 1.6c)

| Patient | Evidence | Note |
|---|---|---|
| **DEMO-007** | `CONV-007` (transcript) vs `MED-018` (active Warfarin) | Prior-visit transcript: patient reports they **stopped taking Warfarin** a few weeks ago, but `MED-018` still reads `active` → **contradiction** → drives SURFACE/VERIFY via transcript evidence. Key demo case. |
| **DEMO-016** | `CONV-016` (transcript) | Benign routine check-in, no complaints, no contradiction → search returns non-alarming results too. |

`conversation_transcript` rows are authored via `db/seed_conversations.sql` (idempotent) and read only
by `search_conversations` (ILIKE over `transcript_text` + `summary`). Transcripts describe what was said —
no diagnosis, no treatment advice.
