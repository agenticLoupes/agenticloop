// SHARED CONTRACT. Mirror of backend/schemas.py. Frozen 2026-09-19 14:45 CDT.
// Change one, change both, in the same PR.
//
// POST /frame  {session_id, data:<b64 JPEG>, ts}                 -> {ok}
// POST /turn   {session_id, patient_id, transcript, speaker}      -> TurnOut
// GET  /flags?session_id=&since=<last flag id>                     -> {flags:[Flag]}
//
// Box   {tooth, x, y, w, h, conf, highlight, label}   coords 0-1, origin top-left
// Flag  {id, tooth, severity:'info'|'watch'|'stop', message, basis:[str], created_at}
// TurnOut {reply, boxes:[Box], findings_logged, flag:Flag|null, latency_ms}

const BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export const SESSION_ID = import.meta.env.VITE_SESSION_ID ?? "demo-1";
export const PATIENT_ID = import.meta.env.VITE_PATIENT_ID ?? "P-88204";
export const WAKE_PHRASE = (import.meta.env.VITE_WAKE_PHRASE ?? "hey loupes").toLowerCase();

async function post(path, body) {
  const r = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`${path} ${r.status}`);
  return r.json();
}

/** Push the newest camera frame. Fire and forget at 1-2 FPS. */
export const sendFrame = (dataB64) =>
  post("/frame", { session_id: SESSION_ID, data: dataB64, ts: Date.now() });

/** Send a wake-word-gated utterance. Strip the wake phrase before calling. */
export const sendTurn = (transcript, speaker = "dentist") =>
  post("/turn", { session_id: SESSION_ID, patient_id: PATIENT_ID, transcript, speaker });

/** Poll for unprompted flags newer than `since` (a flag id, 0 to start). */
export async function pollFlags(since = 0) {
  const r = await fetch(`${BASE}/flags?session_id=${SESSION_ID}&since=${since}`);
  if (!r.ok) throw new Error(`/flags ${r.status}`);
  return (await r.json()).flags;
}

/** Wake-word gate. Returns the utterance with the phrase removed, or null. */
export function gate(transcript) {
  const t = transcript.toLowerCase().replace(/[^a-z0-9 ]/g, " ").replace(/\s+/g, " ").trim();
  const variants = [WAKE_PHRASE, "hey loops", "hey loop", "a loupes", "hey lupus", "hey lopez"];
  for (const v of variants) {
    const i = t.indexOf(v);
    if (i !== -1) return t.slice(i + v.length).trim();
  }
  return null;
}
