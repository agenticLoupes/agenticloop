"""log_finding(tooth, observation, source, confidence) -> {"id": int}

[OWNER: B]  Called AUTONOMOUSLY after every exchange, not on user request.
Writes the row in `session_findings` that makes this an agent. plan.md §1.

source is one of: 'cv' | 'dentist_speech' | 'patient_speech'
"""
