# Agents Track write-up

DentAssist Guardian is our Agents Track proof of concept for autonomous pre-procedure record review.

A dentist selects a synthetic patient, states a planned procedure, and identifies a tooth. From that point, the agent investigates without further prompting. Its memory comes from the patient's longitudinal medical and dental record plus explicit investigation state, rather than hidden conversation history.

The Guardian demonstrates tool use by choosing among nine record tools for the patient summary, dental history, medications, allergies, conditions, notes, conversations, and imaging. It does not call a fixed sequence. A finding can change its reasoning about what to do next, including whether to inspect another source, gather supporting evidence, or stop. That model-directed investigation is the system's autonomous action.

Each candidate then passes to a Skeptic powered by TypeSafe Jev. The Skeptic challenges relevance, recency, contradictions, duplication, patient identity, and source support. It returns `SURFACE`, `DISMISS`, or `VERIFY`, so weak evidence can be dismissed and a clean record can produce silence.

Every displayed card cites a record ID that the dentist can open and inspect. The demo uses 100% synthetic patient data, and the seeded images are generated renders. The records contain no PHI. DentAssist Guardian does not diagnose, prescribe, or recommend treatment. It is a proof of concept, not a diagnostic device. The dentist remains responsible for clinical decisions.

<!-- Word count: 219 -->
