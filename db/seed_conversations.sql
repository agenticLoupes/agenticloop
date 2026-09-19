-- Synthetic conversation transcripts (100% synthetic). Patients already exist; do NOT truncate.
-- Idempotent: on conflict (id) do nothing.

insert into conversation_transcript (id, patient_id, transcript_date, participants, transcript_text, summary, source_label, recorded_at) values
(
  'CONV-007','DEMO-007','2026-08-15','Patient, Dr. Nguyen',
  'Dr. Nguyen: Good to see you again. Are you still taking all your usual medications? '
  'Patient: Mostly. I actually stopped taking my blood thinner, the Warfarin, a few weeks ago. '
  'Dr. Nguyen: Okay. Can you say more about that? '
  'Patient: I just ran out and did not refill it. I have not taken it since. '
  'Dr. Nguyen: Thank you for letting me know. I have noted that in your chart.',
  'Patient reports having stopped taking Warfarin (blood thinner) a few weeks prior to this visit.',
  'Synthetic visit transcript','2026-08-15T14:30:00Z'
),
(
  'CONV-016','DEMO-016','2026-07-02','Patient, Dr. Patel',
  'Dr. Patel: How have things been since your last cleaning? '
  'Patient: Pretty good, no complaints. Brushing twice a day and flossing most days. '
  'Dr. Patel: That is great to hear. Any sensitivity or discomfort? '
  'Patient: No, nothing unusual. '
  'Dr. Patel: Wonderful, we will do a routine check today.',
  'Routine check-in; patient reports no complaints and good home care.',
  'Synthetic visit transcript','2026-07-02T09:15:00Z'
)
on conflict (id) do nothing;
