// Same-origin by default: next.config.ts proxies /api/* to FastAPI (works through a tunnel).
export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "/api";

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
  image_url?: string | null;
  image_caption?: string | null;
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
  summary?: string;
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
  // timeout + one retry: a transient network/pool blip self-heals instead of
  // leaving the UI on an endless "Loading…" (fail-safe per PLAN §22)
  for (let attempt = 0; ; attempt++) {
    try {
      const res = await fetch(`${API_URL}${path}`, {
        ...init,
        signal: AbortSignal.timeout(12_000),
      });
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      return (await res.json()) as T;
    } catch (e) {
      if (attempt >= 1) throw e;
      await new Promise((r) => setTimeout(r, 800));
    }
  }
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

export interface ChatTurn {
  role: "dentist" | "assistant";
  content: string;
}

export const askAboutCase = (
  runId: string,
  question: string,
  history: ChatTurn[] = [],
  init?: RequestInit
) =>
  request<{ answer: string }>(`/investigations/${runId}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, history }),
    ...init,
  });

export const resetDemo = () =>
  request<unknown>("/demo/reset", { method: "POST" });

export const uploadImaging = async (
  patientId: string,
  toothNumber: number | null,
  file: File
): Promise<{ record_id: string; image_url: string }> => {
  const form = new FormData();
  form.append("patient_id", patientId);
  if (toothNumber != null) form.append("tooth_number", String(toothNumber));
  form.append("file", file);
  const res = await fetch(`${API_URL}/uploads/imaging`, { method: "POST", body: form });
  if (!res.ok) throw new Error(`${res.status}`);
  return res.json();
};

// ---- live voice (phone /live route) ----------------------------------------

// One-use ephemeral token; the real GOOGLE_API_KEY never leaves the backend.
export interface LiveToken {
  token: string;
  model: string;
  api_version: string;
}

export const getLiveToken = () =>
  request<LiveToken>("/live/token", { method: "POST" });

// Newest run from any device — lets the laptop follow runs started by voice on the phone.
export interface LatestRun {
  id: string;
  patient_id: string;
  procedure: string;
  tooth_number: number | null;
  status: "running" | "complete" | "error";
  started_at: string;
}

export const getLatestRun = () => request<LatestRun | null>("/live/latest-run");

export interface TranscriptLine {
  id: number;
  role: "dentist" | "assistant" | "system";
  text: string;
  at: string;
}

export const getTranscript = (since: number) =>
  request<TranscriptLine[]>(`/live/transcript?since=${since}`);

export const postTranscript = (role: TranscriptLine["role"], text: string) =>
  request<{ id: number | null }>("/live/transcript", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ role, text }),
  });
