"""The autonomous divergence check.  [OWNER: B]  *** plan.md §1 -- never cut ***

Runs after every exchange, unprompted. LangGraph if it's up in 45 min,
otherwise four if-statements in plain Python (plan.md §3.1 time box).

  read session_findings + tooth history -> diverged? -> push a `flag`

Divergence types to cover:
  - periodontal depth worsening vs. prior record
  - restoration aging past expected life
  - a live symptom matching a case pattern
  - allergy / vitals relevant to what's about to happen

TODO:
  - reconcile(session_id, patient_id, tooth) -> Flag | None  (see schemas.py)
"""
