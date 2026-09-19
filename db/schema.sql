-- Agentic Loupes schema. SQLite (default, zero setup) -- also valid Postgres
-- with the two noted swaps. Frozen 2026-09-19 14:45 CDT.
--
-- Backend opens ./loupes.db with `sqlite3` and runs this file then seed.sql on
-- first start. Persistence across sessions is the file itself: that is the memory.
--
-- Postgres swap: INTEGER PRIMARY KEY AUTOINCREMENT -> bigserial primary key
--                allergies TEXT (JSON array)        -> text[]

CREATE TABLE IF NOT EXISTS patients (
  id              TEXT PRIMARY KEY,
  name            TEXT NOT NULL,
  dob             TEXT,                 -- ISO date, synthetic
  bp              TEXT,
  allergies       TEXT NOT NULL DEFAULT '[]',   -- JSON array of strings
  vitals_taken_at TEXT
);

CREATE TABLE IF NOT EXISTS teeth (
  patient_id           TEXT NOT NULL REFERENCES patients(id),
  tooth                TEXT NOT NULL,   -- FDI two-digit as text: '36', not 'FDI_36'
  restoration          TEXT,
  periodontal_depth_mm INTEGER,
  last_treated         TEXT,            -- ISO date
  notes                TEXT,
  xray_url             TEXT,
  PRIMARY KEY (patient_id, tooth)
);

-- Prior periodontal charting. reconcile() compares the latest row against
-- teeth.periodontal_depth_mm to detect worsening.
CREATE TABLE IF NOT EXISTS perio_history (
  id                   INTEGER PRIMARY KEY AUTOINCREMENT,
  patient_id           TEXT NOT NULL REFERENCES patients(id),
  tooth                TEXT NOT NULL,
  periodontal_depth_mm INTEGER NOT NULL,
  measured_on          TEXT NOT NULL    -- ISO date
);

-- The memory. Written autonomously after every turn, read on every turn.
CREATE TABLE IF NOT EXISTS session_findings (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id  TEXT NOT NULL,
  patient_id  TEXT NOT NULL,
  tooth       TEXT NOT NULL,
  observation TEXT NOT NULL,
  source      TEXT NOT NULL CHECK (source IN ('cv','dentist_speech','patient_speech','agent')),
  confidence  REAL NOT NULL DEFAULT 1.0,
  created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

-- Unprompted alerts raised by reconcile(). GET /flags reads this. One row per
-- (session, tooth, kind) -- the UNIQUE index is the per-tooth cooldown.
CREATE TABLE IF NOT EXISTS flags (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id  TEXT NOT NULL,
  patient_id  TEXT NOT NULL,
  tooth       TEXT NOT NULL,
  kind        TEXT NOT NULL,            -- 'perio_worsening' | 'restoration_age' | 'symptom_pattern' | 'allergy'
  severity    TEXT NOT NULL CHECK (severity IN ('info','watch','stop')),
  message     TEXT NOT NULL,
  basis       TEXT NOT NULL DEFAULT '[]',  -- JSON array of citations
  created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  UNIQUE (session_id, tooth, kind)
);

CREATE TABLE IF NOT EXISTS cases (
  id       TEXT PRIMARY KEY,
  summary  TEXT NOT NULL,
  findings TEXT NOT NULL,
  outcome  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_findings_tooth ON session_findings(patient_id, tooth, created_at);
CREATE INDEX IF NOT EXISTS idx_flags_session  ON flags(session_id, id);
