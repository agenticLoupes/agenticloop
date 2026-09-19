-- SYNTHETIC DATA. No PHI. Every row invented for the demo on 2026-09-19.
-- Provenance: db/PROVENANCE.md. One patient, four teeth fully populated.
--
-- The demo depends on tooth 36 (FDI; universal #19) having a composite from
-- 2024, a pocket that went 3mm -> 4mm since March, and a patient with a
-- penicillin allergy. Do not change those three facts without changing
-- demo/script.md.
--
-- FDI <-> Universal for the four demo teeth:  36=#19  37=#18  46=#30  26=#14

INSERT OR REPLACE INTO patients (id, name, dob, bp, allergies, vitals_taken_at) VALUES
  ('P-88204', 'Jordan Okafor (synthetic)', '1984-06-12', '128/82',
   '["penicillin"]', '2026-09-19T13:40:00Z');

INSERT OR REPLACE INTO teeth (patient_id, tooth, restoration, periodontal_depth_mm, last_treated, notes, xray_url) VALUES
  ('P-88204', '36', 'composite, occlusal-distal', 4, '2024-02-14',
   'Distal margin slightly open on last exam. Watch. Pt reports occasional cold sensitivity.', NULL),
  ('P-88204', '37', 'none', 3, '2025-03-02',
   'Prophy only. Mild plaque distal.', NULL),
  ('P-88204', '46', 'amalgam, occlusal', 3, '2011-08-20',
   'Amalgam 15 yrs old, intact margins. Monitor for fracture lines.', NULL),
  ('P-88204', '26', 'porcelain crown', 2, '2022-11-05',
   'Crown seated 2022, no issues.', NULL);

-- Prior charting. Tooth 36 worsened 3 -> 4 mm between March and today.
INSERT INTO perio_history (patient_id, tooth, periodontal_depth_mm, measured_on) VALUES
  ('P-88204', '36', 3, '2025-09-10'),
  ('P-88204', '36', 3, '2026-03-02'),
  ('P-88204', '36', 4, '2026-09-19'),
  ('P-88204', '37', 3, '2026-03-02'),
  ('P-88204', '46', 3, '2026-03-02'),
  ('P-88204', '26', 2, '2026-03-02');

-- Case corpus for pattern matching (used only if find_similar_cases ships).
INSERT OR REPLACE INTO cases (id, summary, findings, outcome) VALUES
  ('C-001', 'Cold sensitivity under 2yr-old posterior composite', 'cold sensitivity; open distal margin; depth 3->4mm', 'Margin repair; sensitivity resolved in 3 weeks'),
  ('C-002', 'Cracked amalgam, lower first molar, 14 yrs old', 'sharp pain on biting; visible fracture line', 'Full-coverage crown'),
  ('C-003', 'Localized pocket deepening, lower first molar', 'depth 3->5mm over 12 months; bleeding on probing', 'Scaling and root planing; re-eval 6 weeks'),
  ('C-004', 'Cold sensitivity, no restoration', 'generalized cold sensitivity; recession', 'Desensitizing agent; monitor'),
  ('C-005', 'Penicillin-allergic pt needing premed', 'penicillin allergy on file; prosthetic joint', 'Clindamycin premed protocol'),
  ('C-006', 'Sensitivity plus worsening pocket, posterior composite', 'cold sensitivity; depth increase 1mm in 6 months; composite 2yr', 'Radiograph; margin evaluation before further restorative work'),
  ('C-007', 'Crown with recurrent decay at margin', 'stain at margin; explorer catch', 'Crown replacement'),
  ('C-008', 'Amalgam replacement, patient preference', 'intact amalgam; esthetic concern', 'Composite replacement'),
  ('C-009', 'Deep pocket, mobility grade 1', 'depth 6mm; mobility', 'Periodontal referral'),
  ('C-010', 'Occlusal wear, bruxism', 'flattened cusps; sensitivity', 'Night guard'),
  ('C-011', 'Sensitivity after recent restoration', 'composite placed 3 weeks ago; cold sensitivity', 'Monitor 6 weeks; resolved'),
  ('C-012', 'Failed composite margin, upper molar', 'open margin; food trapping', 'Replace restoration'),
  ('C-013', 'Pt on anticoagulant, extraction planned', 'warfarin; INR 2.8', 'Coordinate with physician; local hemostatics'),
  ('C-014', 'Sensitivity resolved after occlusal adjustment', 'high spot on new crown; cold and bite sensitivity', 'Adjust occlusion'),
  ('C-015', 'Localized inflammation under crown margin', 'depth 4mm; bleeding; crown 4yr', 'Improve hygiene; re-eval 3 months');
