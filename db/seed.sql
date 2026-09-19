-- DentAssist Guardian — 100% synthetic seed (spec §7/§8). See db/scenarios.md for the map.
-- Idempotent: truncate then insert (also backs POST /demo/reset). Transcript rows are seeded
-- by the dedicated transcript sub-agent (Task 1.6c work).

truncate table agent_event, investigation_run, conversation_transcript, imaging_study,
    clinical_note, allergy, medication, medical_condition, dental_event, patient
    restart identity cascade;

insert into patient (id, demo_identifier, display_name, date_of_birth) values
('DEMO-007','DEMO-007','Synthetic Patient 007','1958-04-12'),
('DEMO-008','DEMO-008','Synthetic Patient 008','1971-09-03'),
('DEMO-009','DEMO-009','Synthetic Patient 009','1983-01-27'),
('DEMO-010','DEMO-010','Synthetic Patient 010','1965-06-19'),
('DEMO-011','DEMO-011','Synthetic Patient 011','1990-11-30'),
('DEMO-012','DEMO-012','Synthetic Patient 012','1949-02-08'),
('DEMO-013','DEMO-013','Synthetic Patient 013','2001-07-22'),
('DEMO-014','DEMO-014','Synthetic Patient 014','1977-03-14'),
('DEMO-015','DEMO-015','Synthetic Patient 015','1988-12-05'),
('DEMO-016','DEMO-016','Synthetic Patient 016','1956-10-11'),
('DEMO-017','DEMO-017','Synthetic Patient 017','1995-05-29'),
('DEMO-018','DEMO-018','Synthetic Patient 018','1962-08-17');

-- ============ DEMO-007 — SURFACE (extraction #30): active Warfarin + Penicillin allergy ============
insert into dental_event (id, patient_id, tooth_number, event_type, event_date, summary) values
('DENT-007A','DEMO-007',30,'root_canal','2023-05-10','Root canal therapy, tooth #30'),
('DENT-007B','DEMO-007',30,'crown','2024-02-18','Crown placed, tooth #30'),
('DENT-007C','DEMO-007',14,'pain_complaint','2025-03-02','Patient reported pain, tooth #14');
insert into medication (id, patient_id, medication_name, status, recorded_at) values
('MED-018','DEMO-007','Warfarin','active','2026-08-10'),
('MED-019','DEMO-007','Cetirizine','active','2026-08-10');
insert into allergy (id, patient_id, substance, reaction, status, recorded_at) values
('ALG-007','DEMO-007','Penicillin','documented reaction','active','2022-01-05');
insert into medical_condition (id, patient_id, condition_name, status, recorded_at) values
('COND-007A','DEMO-007','Atrial fibrillation','active','2021-06-01'),
('COND-007B','DEMO-007','Knee replacement','resolved','2021-04-20');
insert into clinical_note (id, patient_id, note_date, summary) values
('NOTE-007','DEMO-007','2025-11-01','Prior note records a reported medication change; details to confirm.');

-- ============ DEMO-008 — DISMISS (extraction #3): only stale/unrelated candidates ============
insert into dental_event (id, patient_id, tooth_number, event_type, event_date, summary) values
('DENT-008A','DEMO-008',3,'filling','2019-08-01','Composite filling, tooth #3 (old)'),
('DENT-008B','DEMO-008',12,'cleaning','2024-06-15','Routine cleaning');
insert into medication (id, patient_id, medication_name, status, recorded_at, ended_at) values
('MED-008','DEMO-008','Amoxicillin','discontinued','2020-02-01','2020-02-14');
insert into medical_condition (id, patient_id, condition_name, status, recorded_at) values
('COND-008','DEMO-008','Seasonal rhinitis','resolved','2018-05-01');

-- ============ DEMO-009 — VERIFY (extraction #19): note mentions med change, no current status ============
insert into dental_event (id, patient_id, tooth_number, event_type, event_date, summary) values
('DENT-009A','DEMO-009',19,'crown','2022-09-09','Crown, tooth #19');
insert into clinical_note (id, patient_id, note_date, summary) values
('NOTE-009','DEMO-009','2025-10-12','Patient reported changing a blood-thinning medication; current status not documented.');
-- deliberately NO medication row -> current status cannot be established -> VERIFY
insert into imaging_study (id, patient_id, tooth_number, region_label, image_url, source_label, recorded_at) values
('IMG-003','DEMO-009',19,'Lower left — tooth #19 region (low detail)','/assets/imaging/IMG-003.png','Synthetic radiograph','2026-07-15');

-- ============ DEMO-010 — IMAGING (extraction #30): IMG-001 relevant -> SURFACE, IMG-002 irrelevant -> DISMISS ==
insert into dental_event (id, patient_id, tooth_number, event_type, event_date, summary) values
('DENT-010A','DEMO-010',30,'exam','2026-05-01','Routine exam, tooth #30 imaged');
insert into imaging_study (id, patient_id, tooth_number, region_label, image_url, source_label, recorded_at) values
('IMG-001','DEMO-010',30,'Lower right — tooth #30 region','/assets/imaging/IMG-001.png','Synthetic radiograph','2026-08-01'),
('IMG-002','DEMO-010',3,'Upper right — tooth #3 region','/assets/imaging/IMG-002.png','Synthetic radiograph','2026-08-01');

-- ============ DEMO-011..018 — variety (lighter records for different tool paths) ============
insert into medication (id, patient_id, medication_name, status, recorded_at) values
('MED-011','DEMO-011','Lisinopril','active','2026-01-10'),
('MED-013','DEMO-013','Isotretinoin','active','2026-02-01'),
('MED-014','DEMO-014','Metformin','active','2025-03-01'),
('MED-015','DEMO-015','Ibuprofen','active','2026-05-01'),
('MED-016','DEMO-016','Apixaban','active','2026-02-20');
insert into allergy (id, patient_id, substance, reaction, status, recorded_at) values
('ALG-012','DEMO-012','Latex','contact reaction','active','2020-01-01'),
('ALG-014','DEMO-014','Lidocaine','documented reaction','active','2021-06-01'),
('ALG-016','DEMO-016','Aspirin','documented','active','2019-01-01');
insert into medical_condition (id, patient_id, condition_name, status, recorded_at) values
('COND-012','DEMO-012','Latex sensitivity noted at intake','active','2020-01-01'),
('COND-014','DEMO-014','Type 2 diabetes','active','2024-01-01'),
('COND-016','DEMO-016','Hypertension','active','2023-01-01');
insert into imaging_study (id, patient_id, tooth_number, region_label, image_url, source_label, recorded_at) values
('IMG-004','DEMO-011',8,'Upper front — tooth #8 region','/assets/imaging/IMG-004.png','Synthetic radiograph','2026-08-20'),
('IMG-005','DEMO-017',30,'Lower right — tooth #30 region','/assets/imaging/IMG-005.png','Synthetic radiograph','2026-06-10');
insert into dental_event (id, patient_id, tooth_number, event_type, event_date, summary) values
('DENT-013A','DEMO-013',8,'cleaning','2026-04-01','Routine cleaning'),
('DENT-015A','DEMO-015',19,'filling','2025-12-01','Filling, tooth #19'),
('DENT-017A','DEMO-017',30,'exam','2026-03-15','Exam, tooth #30'),
('DENT-018A','DEMO-018',3,'extraction','2020-01-01','Prior extraction, tooth #3');
insert into clinical_note (id, patient_id, note_date, summary) values
('NOTE-011','DEMO-011','2026-01-10','Blood pressure well controlled on current medication.'),
('NOTE-016','DEMO-016','2026-02-20','On anticoagulant; routine monitoring.');
