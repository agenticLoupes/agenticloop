# DentAssist Guardian — Hackathon Master Plan

**Status:** Frozen MVP plan  
**Product type:** Agentic pre-procedure record review prototype  
**Demo data:** 100% synthetic  
**Primary tracks:** Agents + Commercializable  
**Core principle:** **Before you begin, let the record challenge the plan.**

---

## 1. The Project in One Sentence

> **DentAssist Guardian is an autonomous pre-procedure challenge agent that investigates a patient's longitudinal medical and dental record and surfaces evidence the dentist may want to verify before beginning treatment.**

DentAssist is **not** another dental chart, tooth-history viewer, medical-record summary, diagnosis system, or treatment recommendation engine.

Its job is narrower:

> **Given what the dentist is about to do, investigate the available record, find potentially relevant evidence, challenge whether that evidence really deserves attention, and either surface it with sources or stay silent.**

---

## 2. The Problem

Dental records can contain information across multiple areas:

- dental procedures and tooth history;
- medical conditions;
- medications;
- allergies;
- prior notes;
- recent changes in the patient's history.

Existing software can store and display these records. The problem DentAssist demonstrates is different:

> **The dentist still has to know what to look for and where to look for it.**

Immediately before a procedure, DentAssist receives the planned procedure as context and proactively investigates the synthetic record.

The prototype is designed to answer:

> **“Given what I am about to do, which existing records are worth reviewing before I begin?”**

The dentist remains the decision-maker.

---

## 3. Why This Is Different

### Traditional chart

```text
Dentist searches
      ↓
System displays records
```

### RAG/chat assistant

```text
Dentist asks a question
      ↓
System retrieves records
      ↓
System summarizes
```

### DentAssist Guardian

```text
Dentist states procedure intent
      ↓
Guardian plans an investigation
      ↓
Chooses which record sources to inspect
      ↓
Findings can change the next investigation step
      ↓
Candidate evidence is challenged
      ↓
SURFACE / DISMISS / VERIFY
      ↓
Dentist reviews source evidence
```

The differentiator is therefore **proactive, procedure-aware investigation**, not simple retrieval.

---

## 4. The “Why”

### Why does this product exist?

Because the useful information may be distributed across several parts of a longitudinal record, while the dentist's immediate context is a specific procedure.

### Why an agent instead of SQL?

SQL can answer a known query. DentAssist must decide **which query/tool to use next** based on the procedure and what previous tool calls reveal.

Example:

```text
Planned extraction
      ↓
Inspect relevant dental history
      ↓
Prior procedure discovered
      ↓
Inspect related records
      ↓
Inspect active medications
      ↓
Potentially relevant record found
      ↓
Inspect supporting/current records
      ↓
Challenge evidence
```

The path is not defined as “always call every tool in the same order.”

### Why would someone pay?

The commercial hypothesis is that a practice may value a proactive review layer that reduces manual chart searching and brings potentially relevant source records to the dentist's attention at the moment of care.

**Hackathon claim only:** this is a commercial hypothesis, not proven customer demand.

---

# 5. What We Are Building

The MVP proves one complete loop:

```text
PROCEDURE INTENT
       ↓
CONTEXT
       ↓
PLAN INVESTIGATION
       ↓
USE RECORD TOOLS
       ↓
FOLLOW DISCOVERIES
       ↓
PROPOSE CANDIDATE EVIDENCE
       ↓
SKEPTIC / VERIFIER
       ↓
┌────────────┬──────────────┬─────────────┐
│            │              │             │
DISMISS     VERIFY        SURFACE
                              ↓
                    EVIDENCE-BACKED CARD
                              ↓
                       DENTIST REVIEWS
```

Everything else is secondary.

---

# 6. Explicit MVP Boundary

## Build now

- mobile-first web interface;
- synthetic patient selector;
- procedure-intent input;
- tooth number when relevant;
- synthetic dental history;
- synthetic medical conditions;
- synthetic medication records;
- synthetic allergies;
- synthetic clinical notes;
- investigation planner;
- deterministic database tools;
- Guardian agent;
- Skeptic/Verifier;
- evidence-backed output;
- visible agent activity trace;
- at least one positive and one negative demo;
- simple deployment;
- reproducible README.

## Do not build now

- X-ray diagnosis;
- CBCT analysis;
- computer vision;
- model training/fine-tuning;
- real EHR integration;
- physical smart-glasses integration;
- autonomous diagnosis;
- treatment recommendations;
- prescriptions;
- insurance workflows;
- scheduling;
- production HIPAA claims;
- FDA/medical-device claims;
- production clinical validation;
- custom realtime infrastructure;
- custom WebSocket/SSE servers.

If the core demo is not reliable, none of these are allowed to enter scope.

---

# 7. Demo Data

Use **100% synthetic records**.

Create approximately **12 patients** with deliberately controlled scenarios.

Minimum data domains:

```text
Patient
DentalEvent
MedicalCondition
Medication
Allergy
ClinicalNote
ProcedureIntent
Evidence
InvestigationRun
AgentEvent
```

## Example synthetic patient

```text
Patient: DEMO-007

Planned procedure:
Extraction — Tooth #30

Dental history:
2023 — Root canal, tooth #30
2024 — Crown, tooth #30
2025 — Pain complaint, tooth #14

Medical conditions:
Atrial fibrillation
Knee replacement — 2021

Medications:
Warfarin — active
Cetirizine — active

Allergies:
Penicillin

Notes:
Previous note records a reported medication change.
```

The demo must never imply these are real patients.

Visible UI label:

> **SYNTHETIC DATA — PROTOTYPE**

---

# 8. Demo Scenarios

Do not rely on one perfect demo.

## Scenario A — Surface

The planned procedure has record context that the Guardian determines deserves review.

Expected result:

```text
BEFORE YOU BEGIN

2 RECORDS TO VERIFY

Medication
Warfarin — listed as active
[View source]

Allergy
Penicillin — documented
[View source]
```

The prototype should say **why the record was selected for review**, without making a diagnosis or treatment instruction.

## Scenario B — Dismiss

The record contains lots of history, but the candidate is unrelated, stale, contradicted, duplicated, or insufficiently connected to the procedure.

Expected result:

```text
REVIEW COMPLETE

No additional record was surfaced.
3 candidate items were dismissed after verification.

[View investigation]
```

## Scenario C — Verify

The system discovers something potentially relevant but cannot establish enough context.

Expected result:

```text
VERIFY RECORD

A medication change is mentioned in a prior note,
but the current medication status cannot be established.

[View source]
```

This is stronger than inventing certainty.

---

# 9. Agent Architecture

Keep the number of agents small.

## 9.1 Context Interpreter

Input:

```json
{
  "patient_id": "DEMO-007",
  "procedure": "extraction",
  "tooth_number": 30
}
```

Responsibilities:

- normalize explicit procedure intent;
- preserve patient/tooth identifiers;
- identify missing required context;
- never invent missing patient facts.

Output is structured context.

---

## 9.2 Guardian Investigator

This is the primary agent.

Mission:

> **Investigate the available patient record for information that may deserve the dentist's review in the context of the stated procedure.**

The Guardian receives a set of tools. It decides:

- which source to inspect first;
- whether a finding requires another tool call;
- whether enough evidence exists;
- which records become candidate evidence;
- when to stop.

It does **not** diagnose or prescribe.

---

## 9.3 Skeptic / Verifier

Guardian tries to justify surfacing a record.

Skeptic tries to prevent weak or unsupported interruptions.

For every candidate, check:

1. Is it actually this patient?
2. Is the source record real in our database?
3. Is it relevant to the stated procedure/context?
4. Is the information current enough to present as current?
5. Is newer evidence contradictory?
6. Is it a duplicate of another candidate?
7. Does the proposed card say more than the source supports?
8. Can the UI link directly to the evidence?

Outcomes:

```text
SURFACE
DISMISS
VERIFY
```

No arbitrary confidence percentages.

---

## 9.4 Assist Composer

This is formatting, not medical reasoning.

It converts approved evidence into a concise UI card.

Example:

```text
RECORD TO REVIEW

Medication
Warfarin — listed as active

Reason shown:
Selected from the current medication record
during pre-procedure review.

Source:
Medication record MED-018

[View evidence]
```

---

# 10. The Critical Agentic Requirement

The system must **not** simply execute:

```text
get_dental_history()
get_conditions()
get_medications()
get_allergies()
get_notes()
```

in a hard-coded sequence for every patient.

That would be workflow automation, not a convincing agent demonstration.

Instead:

```text
Procedure intent
      ↓
Guardian chooses Tool A
      ↓
observes result
      ↓
result changes next action
      ↓
Guardian chooses Tool C
      ↓
observes result
      ↓
may choose Tool B or stop
```

The UI's Agent Trace should make these choices visible.

---

# 11. Deterministic Tool Layer

The LLM does not invent patient facts.

Suggested tools:

```text
get_patient_summary(patient_id)

get_dental_history(
    patient_id,
    tooth_number=null,
    event_types=null
)

get_active_medications(patient_id)

get_medication_history(
    patient_id,
    medication_name=null
)

get_allergies(patient_id)

get_medical_conditions(
    patient_id,
    status=null
)

search_clinical_notes(
    patient_id,
    query,
    from_date=null,
    to_date=null
)

get_record(record_type, record_id)
```

Every returned record has:

```json
{
  "record_id": "MED-018",
  "record_type": "medication",
  "patient_id": "DEMO-007",
  "source_label": "Synthetic medication record",
  "recorded_at": "2026-08-10T00:00:00Z",
  "data": {}
}
```

The model may interpret tool results, but it cannot create a patient fact without a source record.

---

# 12. Evidence Contract

Every candidate and every surfaced card must contain evidence IDs.

Core rule:

> **NO EVIDENCE ID → NO FACTUAL CARD**

Example:

```json
{
  "decision": "SURFACE",
  "title": "Medication record to review",
  "summary": "Warfarin is listed as active.",
  "reason_shown": "Selected during pre-procedure record review.",
  "evidence_ids": ["MED-018"]
}
```

Clicking the card must display the underlying synthetic record.

---

# 13. Investigation State

Use explicit application state.

```json
{
  "run_id": "uuid",
  "patient_id": "uuid",
  "procedure": "extraction",
  "tooth_number": 30,
  "investigation_goal": "pre_procedure_review",
  "tool_calls": [],
  "observations": [],
  "candidate_evidence": [],
  "skeptic_results": [],
  "final_cards": [],
  "status": "running"
}
```

Do not rely on hidden conversation history as the source of application state.

---

# 14. Recommended Stack

## Frontend

```text
Next.js
TypeScript
Tailwind CSS
```

Mobile-first responsive PWA/web application.

## Backend

```text
FastAPI
Python
```

## Agent orchestration

```text
LangGraph
```

Use LangGraph for stateful tool-calling and branching. Do not build an agent runtime.

Official documentation:
https://docs.langchain.com/oss/python/langgraph/overview

## Inference

```text
Featherless
```

Use an OpenAI-compatible provider adapter.

Do not expose the model API key in the browser.

Official:
https://featherless.ai/docs/quickstart-guide
https://featherless.ai/docs/tool-calling

## Database

```text
Supabase PostgreSQL
```

Use it primarily as PostgreSQL for the hackathon.

Do **not** make database-triggered realtime/reconnect infrastructure part of the critical path.

Official:
https://supabase.com/docs/guides/database/overview

---

# 15. Simplified Request Flow

For this hackathon, optimize for reliability rather than production architecture.

```text
Next.js
   ↓
POST /investigations
   ↓
FastAPI
   ↓
LangGraph
   ↓
Featherless + deterministic tools
   ↓
Supabase PostgreSQL
   ↓
Structured investigation result
   ↓
Next.js
```

For the visible trace, the simplest implementation is acceptable:

```text
POST investigation
       ↓
backend runs graph
       ↓
persist/collect trace events
       ↓
return result + trace
       ↓
frontend animates trace
```

If incremental status is easy, use lightweight polling:

```text
POST /investigations
GET /investigations/{id}
```

Do not spend hackathon time building production-grade streaming.

---

# 16. Minimal API

```text
GET  /health

GET  /demo/patients

GET  /patients/{patient_id}

POST /investigations

GET  /investigations/{run_id}

GET  /investigations/{run_id}/trace

GET  /evidence/{record_type}/{record_id}

POST /demo/reset
```

Example request:

```json
{
  "patient_id": "DEMO-007",
  "procedure": "extraction",
  "tooth_number": 30
}
```

---

# 17. Minimal Database Schema

## patient

```text
id
demo_identifier
display_name
date_of_birth
created_at
```

## dental_event

```text
id
patient_id
tooth_number
event_type
event_date
summary
metadata
```

## medical_condition

```text
id
patient_id
condition_name
status
recorded_at
metadata
```

## medication

```text
id
patient_id
medication_name
status
recorded_at
ended_at
metadata
```

## allergy

```text
id
patient_id
substance
reaction
status
recorded_at
metadata
```

## clinical_note

```text
id
patient_id
note_date
summary
metadata
```

## investigation_run

```text
id
patient_id
procedure
tooth_number
status
result
started_at
completed_at
```

## agent_event

```text
id
run_id
sequence_no
agent
event_type
summary
metadata
created_at
```

Do not create additional tables unless implementation actually requires them.

---

# 18. Synthetic Data Strategy

No model training dataset is needed.

For the MVP, controlled synthetic records are preferable because the demo requires known positive, negative, contradictory, and uncertain cases.

Optional resource:

**Synthea** generates synthetic health records and supports FHIR exports.

Official:
https://synthea.mitre.org/
https://synthea.mitre.org/downloads

Use Synthea only if it accelerates development. Do not let data import become a project of its own.

A practical approach:

```text
Synthetic general medical structure
            +
Hand-authored dental scenarios
            ↓
     DentAssist demo DB
```

---

# 19. FHIR Strategy

Do not deploy a FHIR server for the MVP.

Use FHIR concepts as an interoperability direction:

```text
Patient
AllergyIntolerance
Condition
MedicationRequest / MedicationStatement-style data
Observation / clinical-note references
```

Long-term, create adapters between EHR/PMS records and DentAssist's normalized internal tool schema.

Official HL7 FHIR:
https://hl7.org/fhir/

Optional reference implementation:
https://hapifhir.io/

---

# 20. UI

## Screen 1 — Patient

```text
DENTASSIST GUARDIAN
SYNTHETIC DATA — PROTOTYPE

Select demo patient

DEMO-007
DEMO-008
DEMO-009
...
```

## Screen 2 — Procedure intent

```text
What are you about to do?

Procedure
[ Extraction ▼ ]

Tooth
[ #30 ▼ ]

[ CHALLENGE PROCEDURE ]
```

Voice can be visually suggested but is not required.

## Screen 3 — Investigation

```text
CHALLENGING PROCEDURE...

Guardian
✓ Reviewed tooth #30 history

Guardian
✓ Found prior procedure record

Guardian
→ Checking related patient context

Guardian
✓ Reviewed active medication record

Skeptic
→ Challenging 3 candidate records

Skeptic
✓ Dismissed 1
! 1 requires verification
✓ 1 approved for review
```

Only show observable actions. Do not expose hidden chain-of-thought.

## Screen 4 — Result

```text
BEFORE YOU BEGIN

1 RECORD TO REVIEW

Medication
Warfarin — listed as active

Why shown?
Selected during the pre-procedure
record review.

[ VIEW SOURCE ]
```

## Screen 5 — Evidence

```text
SOURCE RECORD

Record: MED-018
Type: Medication
Patient: DEMO-007
Status: Active
Recorded: Aug 10, 2026

Synthetic medication record
```

---

# 21. Safe Product Language

Use:

- “Record to review”
- “Item to verify”
- “Relevant record located”
- “Selected during pre-procedure review”
- “Source evidence”
- “Current status could not be established”
- “No additional record surfaced”

Avoid:

- “Unsafe procedure”
- “Do not perform”
- “Diagnosis”
- “You should prescribe”
- “Recommended treatment”
- “The patient definitely has”
- “Clinically validated”
- “HIPAA compliant” unless actually established
- unsupported claims that DentAssist prevents malpractice or adverse events.

---

# 22. Failure Behavior

| Situation | Required behavior |
|---|---|
| Patient missing | Stop |
| Procedure missing | Ask for procedure |
| Tooth required but missing | Ask for tooth |
| Tool fails | Report unavailable source; do not invent result |
| Record has uncertain status | VERIFY |
| Evidence contradicts candidate | DISMISS or VERIFY |
| Evidence ID missing | Do not surface factual card |
| Model output invalid | Validate/retry once, then fail safely |
| No relevant evidence | Return no-interruption result |
| Provider unavailable | Show recoverable demo error |

Silence is a valid successful outcome.

---

# 23. What the Judges Must See

Within the first minute, the judge should understand:

1. what procedure the dentist intends to perform;
2. that the agent chooses what to investigate;
3. that findings alter subsequent tool use;
4. that the system rejects weak candidates;
5. that the final card links to source evidence.

Do not spend demo time explaining database infrastructure.

---

# 24. Demo Script

## 0:00–0:20 — Problem

> “Dental systems contain a lot of patient information, but they generally wait for the clinician to look for it. DentAssist Guardian starts with what the dentist is about to do and proactively investigates the available record for information worth reviewing.”

## 0:20–0:35 — Product

> “Instead of summarizing the whole chart, Guardian chooses which records to inspect, follows relevant findings, challenges its own candidates, and stays silent when the evidence isn't strong enough.”

Show:

```text
SYNTHETIC DATA — PROTOTYPE
```

## 0:35–1:30 — Positive investigation

Choose DEMO-007.

Enter:

```text
Extraction
Tooth #30
```

Press:

```text
CHALLENGE PROCEDURE
```

Show agent trace and final evidence-backed card.

Open its source record.

## 1:30–2:05 — Negative/uncertain investigation

Run a second patient.

Show that Guardian retrieves information but Skeptic dismisses it or marks it VERIFY.

Say:

> “The product isn't trying to maximize alerts. Its job is to decide what deserves the dentist's attention and what doesn't.”

## 2:05–2:30 — Architecture

```text
Next.js
   ↓
FastAPI
   ↓
LangGraph
   ↓
Featherless
   ↕
Deterministic patient-record tools
   ↓
Supabase PostgreSQL
```

## 2:30–2:50 — Future

> “Today the interface is mobile and all data is synthetic. The intelligence layer can later connect to interoperable clinical systems and hands-free interfaces.”

## Close

> **“Before you begin, let the record challenge the plan.”**

---

# 25. Build Order

## Phase 1 — Data

1. Create Supabase project.
2. Create minimal schema.
3. Seed 12 synthetic patients.
4. Create positive, dismiss, and verify scenarios.
5. Implement deterministic queries.
6. Verify every demo record manually.

### Gate 1

The API/tool layer can retrieve every expected source record by ID.

---

## Phase 2 — Agent Core

7. Create FastAPI service.
8. Define investigation state.
9. Define tool schemas.
10. Create Featherless provider adapter.
11. Test one model for reliable structured/tool output.
12. Implement Context Interpreter.
13. Implement Guardian.
14. Implement Skeptic.
15. Implement Assist Composer.
16. Assemble LangGraph.

### Gate 2

From terminal/API:

- Scenario A returns `SURFACE`.
- Scenario B returns `DISMISS`.
- Scenario C returns `VERIFY`.
- every factual result has evidence IDs.

---

## Phase 3 — Prove Real Agency

17. Record tool calls.
18. Ensure different scenarios produce different tool paths.
19. Ensure findings can trigger another tool call.
20. Ensure the model can decide to stop.
21. Ensure the agent does not simply call every tool.

### Gate 3

Two demo patients visibly produce different investigation paths.

This gate is essential for the Agents track.

---

## Phase 4 — UI

22. Build patient selector.
23. Build procedure/tooth form.
24. Build investigation screen.
25. Build judge-visible Agent Trace.
26. Build result cards.
27. Build evidence drawer.
28. Add synthetic-data banner.
29. Add demo reset.

### Gate 4

Complete flow works from a phone/browser without terminal interaction.

---

## Phase 5 — Reliability

30. Run Scenario A five times.
31. Run Scenario B five times.
32. Run Scenario C five times.
33. Verify no unsupported record appears.
34. Verify every card opens its evidence.
35. Verify errors fail safely.

### Gate 5

Five consecutive full demo runs succeed.

---

## Phase 6 — Submission

36. Deploy frontend/backend.
37. Publish public repository.
38. Write quick-start README.
39. Add architecture diagram.
40. Add `.env.example`.
41. Document synthetic-data provenance.
42. Document limitations.
43. Record 2–5 minute demo.
44. Complete project write-up.
45. Submit.

---

# 26. Time-Priority Rule

If time becomes limited, preserve work in this order:

```text
1. Real agent investigation
2. Evidence correctness
3. SURFACE / DISMISS / VERIFY
4. Working UI
5. Agent trace
6. Deployment
7. Visual polish
8. Optional integrations
```

Never trade the working agent loop for cosmetic features.

---

# 27. Definition of Done

The hackathon MVP is complete only when:

- a synthetic patient can be selected;
- a procedure can be specified;
- Guardian autonomously selects record tools;
- discoveries can change the next tool call;
- different cases produce different tool paths;
- Guardian produces candidate evidence;
- Skeptic can SURFACE, DISMISS, and VERIFY;
- every factual card has evidence IDs;
- every evidence ID opens a real synthetic DB record;
- no diagnosis/treatment recommendation is generated;
- no real patient information is used;
- the entire flow works in the deployed UI;
- the demo works repeatedly;
- README reproduces the project.

---

# 28. Future Architecture — Not Hackathon Scope

Only after the MVP:

## Wearables

Meta Wearables Device Access Toolkit can be evaluated as a future hands-free interface.

Official:
https://developers.meta.com/wearables/

Meta's Mock Device Kit can support development without physical hardware, but current documentation notes limitations around display-glasses simulation. Do not depend on it for the hackathon UI.

Official FAQ:
https://developers.meta.com/wearables/faq/

## Imaging

Do not build a medical image viewer.

Use OHIF/Cornerstone3D if future work requires DICOM/DICOMWeb visualization.

Official:
https://docs.ohif.org/

## Medical multimodal models

MedGemma can be evaluated for future medical text/image research. It is not part of this MVP and requires use-case-specific validation.

Official:
https://deepmind.google/models/gemma/medgemma/

## Dental CBCT research

ToothFairy2 can be evaluated as a future public dental/maxillofacial CBCT research dataset.

Official:
https://toothfairy2.grand-challenge.org/dataset/

---

# 29. Commercialization Roadmap

The hackathon does **not** prove product-market fit.

The next validation steps would be:

```text
Prototype
   ↓
Dentist workflow interviews
   ↓
Identify highest-value pre-procedure checks
   ↓
Measure alert usefulness / interruption burden
   ↓
PMS/EHR interoperability prototype
   ↓
Clinical + regulatory evaluation
   ↓
Pilot
   ↓
Wearable / chairside interfaces
```

Do not claim dentists will pay until this is validated with actual users.

---

# 30. Final Positioning

Do **not** pitch:

> “AI that reads dental history.”

Do **not** pitch:

> “A chatbot for dentists.”

Do **not** pitch:

> “AI that tells dentists what treatment to perform.”

Pitch:

> **DentAssist Guardian is an autonomous pre-procedure challenge agent. It starts with what the dentist is about to do, investigates the patient's available longitudinal record, follows evidence across relevant sources, challenges its own findings, and surfaces only source-backed records worth reviewing.**

## Tagline

> **Before you begin, let the record challenge the plan.**

## Product principle

> **Investigate broadly. Challenge aggressively. Surface narrowly.**

---

# 31. Sources

Primary references used to guide implementation and avoid rebuilding commodity infrastructure:

- LangGraph documentation — https://docs.langchain.com/oss/python/langgraph/overview
- Featherless quickstart — https://featherless.ai/docs/quickstart-guide
- Featherless tool calling — https://featherless.ai/docs/tool-calling
- Supabase Database — https://supabase.com/docs/guides/database/overview
- Synthea — https://synthea.mitre.org/
- Synthea downloads — https://synthea.mitre.org/downloads
- HL7 FHIR — https://hl7.org/fhir/
- HAPI FHIR — https://hapifhir.io/
- Meta Wearables developer platform — https://developers.meta.com/wearables/
- Meta Wearables FAQ — https://developers.meta.com/wearables/faq/
- OHIF documentation — https://docs.ohif.org/
- MedGemma — https://deepmind.google/models/gemma/medgemma/
- ToothFairy2 dataset — https://toothfairy2.grand-challenge.org/dataset/

---

# 32. Frozen Rule

Once implementation starts, do not redesign the product unless a technical blocker makes the core loop impossible.

The team should repeatedly ask only:

> **Does this task help us prove that Guardian autonomously investigates the record, challenges its findings, and surfaces only evidence worth reviewing?**

If the answer is **no**, it is not part of today's build.
