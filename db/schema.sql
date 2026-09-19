-- DentAssist Guardian — minimal schema (spec §17 + user-approved imaging & transcripts)
-- 100% synthetic data. Patient key is the demo identifier (e.g. DEMO-007) for legibility.
-- Record tables use human-readable text ids (MED-018, IMG-001, ...) so evidence IDs are legible (§12).

create table if not exists patient (
    id             text primary key,          -- demo identifier, e.g. DEMO-007
    demo_identifier text not null,             -- mirrors id for clarity
    display_name   text,
    date_of_birth  date,
    created_at     timestamptz not null default now()
);

create table if not exists dental_event (
    id          text primary key,              -- DENT-###
    patient_id  text not null references patient(id) on delete cascade,
    tooth_number int,
    event_type  text not null,
    event_date  date,
    summary     text,
    metadata    jsonb not null default '{}'::jsonb
);

create table if not exists medical_condition (
    id            text primary key,            -- COND-###
    patient_id    text not null references patient(id) on delete cascade,
    condition_name text not null,
    status        text check (status in ('active','resolved')),  -- fail loud on typo, not silent-wrong
    recorded_at   timestamptz,
    metadata      jsonb not null default '{}'::jsonb
);

create table if not exists medication (
    id             text primary key,           -- MED-###
    patient_id     text not null references patient(id) on delete cascade,
    medication_name text not null,
    status         text check (status in ('active','discontinued')),  -- get_active_medications depends on exact match
    recorded_at    timestamptz,
    ended_at       timestamptz,
    metadata       jsonb not null default '{}'::jsonb
);

create table if not exists allergy (
    id          text primary key,              -- ALG-###
    patient_id  text not null references patient(id) on delete cascade,
    substance   text not null,
    reaction    text,
    status      text check (status in ('active','resolved')),
    recorded_at timestamptz,
    metadata    jsonb not null default '{}'::jsonb
);

create table if not exists clinical_note (
    id         text primary key,               -- NOTE-###
    patient_id text not null references patient(id) on delete cascade,
    note_date  date,
    summary    text,
    metadata   jsonb not null default '{}'::jsonb
);

-- user-approved: synthetic radiographs / intraoral images (locate + relevance only)
create table if not exists imaging_study (
    id           text primary key,             -- IMG-###
    patient_id   text not null references patient(id) on delete cascade,
    tooth_number int,
    region_label text,                         -- authored ground truth (fail-safe gate); NULL for uploads → VERIFY-only
    image_url    text not null,
    source_label text,
    recorded_at  timestamptz,
    metadata     jsonb not null default '{}'::jsonb
);

-- user-approved: prior-visit conversation transcripts as a searchable evidence source
create table if not exists conversation_transcript (
    id             text primary key,           -- CONV-###
    patient_id     text not null references patient(id) on delete cascade,
    transcript_date date,
    participants   text,
    transcript_text text not null,
    summary        text,
    source_label   text,
    recorded_at    timestamptz,
    metadata       jsonb not null default '{}'::jsonb
);

create table if not exists investigation_run (
    id           uuid primary key default gen_random_uuid(),
    patient_id   text not null references patient(id) on delete cascade,
    procedure    text not null,
    tooth_number int,
    status       text not null default 'running',
    result       jsonb,
    started_at   timestamptz not null default now(),
    completed_at timestamptz
);

create table if not exists agent_event (
    id          uuid primary key default gen_random_uuid(),
    run_id      uuid not null references investigation_run(id) on delete cascade,
    sequence_no int not null,
    agent       text not null,                 -- context_interpreter | guardian | skeptic | composer
    event_type  text not null,                 -- tool_call | observation | decision | ...
    summary     text,
    metadata    jsonb not null default '{}'::jsonb,
    created_at  timestamptz not null default now()
);

create index if not exists idx_dental_event_patient on dental_event(patient_id);
create index if not exists idx_medication_patient on medication(patient_id);
create index if not exists idx_allergy_patient on allergy(patient_id);
create index if not exists idx_medical_condition_patient on medical_condition(patient_id);
create index if not exists idx_clinical_note_patient on clinical_note(patient_id);
create index if not exists idx_imaging_study_patient on imaging_study(patient_id);
create index if not exists idx_conversation_transcript_patient on conversation_transcript(patient_id);
create index if not exists idx_investigation_run_patient on investigation_run(patient_id);
-- unique: agent trace ordering must be unambiguous per run (rejects duplicate steps at the DB)
create unique index if not exists idx_agent_event_run_seq on agent_event(run_id, sequence_no);
