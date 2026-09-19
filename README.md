# Agentic Loupes

AI assistant for dentists. Sees what the dentist sees through their loupes,
hears the room, answers on a wake word with patient-specific context, and
remembers what it found.

> **GRADED deliverable.** Required sections below are from the rules verbatim
> (plan.md §8). Write at T+4:30, not T+5:55. Verify the repo is publicly
> viewable in an incognito window before submitting.

## Quick start
<!-- exact copy-pasteable commands. plan.md §12 -->

```bash
git clone https://github.com/agenticLoupes/agenticloop.git && cd agenticloop
cp .env.example .env          # add OPENAI_API_KEY

cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && uvicorn main:app --reload --port 8000
# first start creates ./loupes.db from ../db/schema.sql + ../db/seed.sql

cd ../frontend && bun install && bun run dev -- --host
# open the printed URL in Chrome (Web Speech API); allow camera + mic
```

## Tech stack & architecture
<!-- paste the ASCII diagram from plan.md §4. Simple is fine. -->

## How to reproduce the demo
<!-- env vars, API keys, sample .env -->

## Datasets, synthetic data & provenance
<!-- link db/PROVENANCE.md. State clearly: patient data is synthetic and
     contains no PHI. This matters in a health demo. -->

## Known limitations & next steps
<!-- Specific and honest -- this section GAINS points, vagueness loses them:
     Roboflow model trained on ~1.4k images; MedGemma is not dental-trained;
     no de-identifying gateway yet; not a diagnostic device. -->
