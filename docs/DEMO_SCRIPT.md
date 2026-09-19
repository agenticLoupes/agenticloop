# DentAssist Guardian — demo script (2:50, Agents Track)

Word for word. Every beat names the patient, the inputs, and what must be on screen.
Grounded in main at `971f099` and the scenario sweep (`docs/SCENARIOS.md`).
Total runtime target: 2:50. Hard cap 3:00.

## Before you press record

```bash
.claude/skills/verify-dentassist/scripts/verify.sh launch
.claude/skills/verify-dentassist/scripts/verify.sh doctor
```

- Laptop: `http://localhost:3000` in an incognito window, zoomed so the phone-width app fills the frame.
- Phone (voice beat only): same LAN, open `http://<laptop-ip>:3000/live`. Mic and camera permissions accepted beforehand.
- Do NOT press "Reset demo" once recording starts.
- Rehearse each patient twice. Investigations take 7 to 26 s. Leave the trace on screen while it runs: that is the product.
- If a run lands on "Recoverable demo error", press Retry once. It shows no invented result, which is itself a safe thing to say out loud.

## 0:00–0:15 — Who we are

Screen: patient list, header reading "DentAssist Guardian. Before you begin, let the record challenge the plan." Footer reads "Synthetic data — prototype".

> "We're DentAssist Guardian, Agents Track. Dental records hold a lot, but the system waits for the dentist to go looking. Guardian starts from what the dentist is about to do and investigates the record first."

> "Everything you'll see is synthetic data. This is a proof of concept, not a diagnostic device."

## 0:15–0:30 — What makes it agentic

> "Guardian doesn't summarize the chart. It picks which records to open, follows what it finds, and then a second agent, the Skeptic, challenges every candidate. If the evidence isn't strong enough, it stays quiet."

## 0:30–1:15 — Beat 1: the positive case

Patient: **DEMO-014** (tag ALLERGY, hint "Documented lidocaine reaction + diabetes").

Tap DEMO-014. The procedure form pre-fills:

```text
Procedure: filling
Tooth: 12
```

Press **Challenge procedure**.

> "I'm about to place a filling on tooth twelve. Watch the trace."

Screen: TraceView. Point at the steps as they appear: context interpreter, Guardian tool calls, Guardian candidates, Skeptic challenge, Skeptic decisions, Composer cards.

> "Guardian is calling deterministic record tools, meds, allergies, notes, imaging. It proposes candidates. The Skeptic argues against each one. Only survivors become cards."

Expected result in about 10 s: three "Record to review" cards. Lidocaine reaction, Type 2 diabetes, active Metformin. Tap **View source** on the Lidocaine card.

> "Every card links to the exact record. A documented lidocaine reaction, before I pick an anesthetic. No hallucinated summaries. The source is one tap away."

## 1:15–1:50 — Beat 2: the honest case

Press "← All patients". Tap **DEMO-009** (tag VERIFY, hint "A note mentions a medication change; current status unknown").

```text
Procedure: extraction
Tooth: 19
```

Press **Challenge procedure**.

> "Extraction, tooth nineteen. This one shows the part we're proudest of."

Expected in about 10 s: one "Record to review" card (the tooth 19 radiograph) and one **"Item to verify"** card on the clinical note.

> "A note says the patient's blood thinner changed. There is no medication row that confirms it. Guardian doesn't guess. It says: verify this before you start. The product isn't trying to maximize alerts. Its job is to decide what deserves the dentist's attention and what doesn't."

Backup if DEMO-009 misbehaves: **DEMO-012**, root_canal, tooth 9. Two "Record to review" cards (latex allergy plus matching intake condition), about 9 s. Say the latex line instead.

## 1:50–2:15 — Beat 3: hands-free (optional, cut if over time)

Phone on camera, `/live` page. Select DEMO-014 in the dropdown, press **Go live**. Status pill turns to LIVE.

Say into the phone:

> "Loupes, I'm doing a filling on tooth twelve."

Screen (laptop): the "Live conversation" panel appears under the header, then the Guardian run status on the phone reads "reviewing the record…" and lands on "3 items to review".

> "Same agents, driven by voice. Gloves on, hands off the keyboard, results on the laptop."

If the live session doesn't connect within 10 s, press End and skip to the architecture beat. Do not retry on camera.

## 2:15–2:30 — Architecture

Screen: this block, full frame.

```text
Next.js (phone-width UI, /live voice page)
   ↓
FastAPI
   ↓
LangGraph: Context Interpreter → Guardian → Skeptic → Composer
   ↓                                      ↕
Gemini (reasoning + Live voice)     deterministic patient-record tools
   ↓
Supabase Postgres (synthetic patients, evidence ids)
```

> "Next.js, FastAPI, LangGraph. Gemini does the reasoning and the voice session. The record tools are deterministic, so every card traces back to a row."

## 2:30–2:50 — Go to market

> "We start with independent practices, where the dentist owner makes both the clinical and the purchasing decision. We sell a per-provider SaaS subscription, an operating expense, not a capital purchase. We prove chairside value through pilots with ten to twenty local practices, capturing time saved and testimonials. Then we scale through practice-management integrations into small groups and DSOs."

## Close

Screen: patient list, header visible.

> "Before you begin, let the record challenge the plan."

## What not to say

- Do not promise specific cards on DEMO-007. Its transcript contradiction card appears in roughly half of runs (#32) and a stray uploaded image can add an unrelated card (#34).
- On DEMO-008's silence screen say "the agent chose to stay quiet." Do not say "candidates were dismissed after verification" (#31: nothing was actually dismissed).
- Never say "diagnosis", "recommendation", or "alert". Say "record to review" and "item to verify", the words on the cards.

## Timing sheet (fill in during rehearsal)

| Beat | Patient | Rehearsal 1 (s) | Rehearsal 2 (s) | Notes |
|---|---|---|---|---|
| 1 | DEMO-014 filling #12 | | | |
| 2 | DEMO-009 extraction #19 | | | |
| 2b backup | DEMO-012 root_canal #9 | | | |
| 3 | /live DEMO-014 | | | |
