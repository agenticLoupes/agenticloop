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

## Transcript scenario (added by the transcript sub-agent — Task 1.6c)
A patient will get a `conversation_transcript` where the patient reports stopping an anticoagulant
while a medication row still reads "active" → contradiction → SURFACE/VERIFY via transcript evidence.
