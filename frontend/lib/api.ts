export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface Patient {
  id: string;
  demo_identifier: string;
  display_name: string;
}

export interface ResultCard {
  decision: "SURFACE" | "VERIFY";
  title: string;
  summary: string;
  reason_shown: string;
  evidence_ids: string[];
}

export interface InvestigationState {
  run_id: string;
  patient_id: string;
  procedure: string;
  tooth_number: number | null;
  status: "complete" | "error";
  error: string | null;
  final_cards: ResultCard[];
  skeptic_results: { decision: string; candidate: { title: string } }[];
  dismissed_count: number;
  verify_count: number;
}

export interface TraceEvent {
  sequence_no: number;
  agent: string;
  event_type: string;
  summary: string;
}

export interface EvidenceRecord {
  record_id: string;
  record_type: string;
  patient_id: string;
  source_label: string;
  recorded_at: string;
  data: Record<string, unknown>;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, init);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}

export const getPatients = () => request<Patient[]>("/demo/patients");

// POST returns immediately; the agent runs server-side while the UI polls trace + status.
export interface RunStart {
  run_id: string;
  status: string;
}

export interface RunRow {
  id: string;
  status: "running" | "complete" | "error";
  result: InvestigationState | null;
}

export const startInvestigation = (body: {
  patient_id: string;
  procedure: string;
  tooth_number: number | null;
}) =>
  request<RunStart>("/investigations", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

export const getRun = (runId: string) =>
  request<RunRow>(`/investigations/${runId}`);

export const getTrace = (runId: string) =>
  request<TraceEvent[]>(`/investigations/${runId}/trace`);

const RECORD_TYPE_BY_PREFIX: Record<string, string> = {
  MED: "medication",
  ALG: "allergy",
  COND: "medical_condition",
  DENT: "dental_event",
  NOTE: "clinical_note",
  IMG: "imaging",
  CONV: "conversation",
};

export const getEvidence = (evidenceId: string) => {
  const type = RECORD_TYPE_BY_PREFIX[evidenceId.split("-")[0]] ?? "record";
  return request<EvidenceRecord>(`/evidence/${type}/${evidenceId}`);
};

export const resetDemo = () =>
  request<unknown>("/demo/reset", { method: "POST" });
