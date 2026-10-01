"use client";

// Phone view: camera + mic, spoken conversation with Gemini Live. Guardian runs it starts
// show up on the laptop (/) automatically; this page shows a compact status.

import { useCallback, useEffect, useRef, useState } from "react";
import { getPatients, postTranscript, type InvestigationState, type Patient } from "@/lib/api";
import { LiveVoice, type LiveStatus } from "@/lib/live/session";
import { TOOL_DECLARATIONS, makeHandlers, systemInstruction } from "@/lib/live/guardianTools";

type Line = { role: "dentist" | "assistant"; text: string };
type Run = {
  procedure: string;
  tooth: number | null;
  state: "running" | "done" | "failed";
  result?: InvestigationState;
};

const STATUS_LABEL: Record<LiveStatus, string> = {
  idle: "Off",
  connecting: "Connecting…",
  live: "Live",
  reconnecting: "Reconnecting…",
  error: "Error",
};

export default function LivePage() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const voiceRef = useRef<LiveVoice | null>(null);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [patient, setPatient] = useState<Patient | null>(null);
  const [status, setStatus] = useState<LiveStatus>("idle");
  const [detail, setDetail] = useState<string | undefined>();
  const [speaking, setSpeaking] = useState(false);
  const [muted, setMuted] = useState(false);
  const [lines, setLines] = useState<Line[]>([]);
  const [run, setRun] = useState<Run | null>(null);

  // tool handlers run inside the socket callbacks; refs give them current state
  const patientRef = useRef(patient);
  patientRef.current = patient;
  const patientsRef = useRef(patients);
  patientsRef.current = patients;

  useEffect(() => {
    getPatients().then(
      (ps) => {
        setPatients(ps);
        setPatient((cur) => cur ?? ps.find((p) => p.id === "DEMO-007") ?? ps[0] ?? null);
      },
      () => setDetail("Backend unreachable — is FastAPI running?")
    );
    return () => void voiceRef.current?.stop(false);
  }, []);

  const addLine = useCallback((role: Line["role"], text: string) => {
    setLines((ls) => [...ls, { role, text }].slice(-8));
    postTranscript(role, text).catch(() => {}); // mirror to the laptop
  }, []);

  const goLive = async () => {
    if (!videoRef.current) return;
    setDetail(undefined);
    const voice: LiveVoice = new LiveVoice({
      systemInstruction: () => systemInstruction(patientRef.current, patientsRef.current),
      tools: TOOL_DECLARATIONS,
      handlers: makeHandlers({
        getPatient: () => patientRef.current,
        getPatients: () => patientsRef.current,
        setPatient,
        onRunStarted: (_id, procedure, tooth) => setRun({ procedure, tooth, state: "running" }),
        onRunFinished: (_id, result) =>
          setRun((r) => r && { ...r, state: result ? "done" : "failed", result: result ?? undefined }),
        notifyModel: (text) => voice.sendText(text),
      }),
      onStatus: (s, d) => {
        setStatus(s);
        setDetail(d);
      },
      onLine: addLine,
      onSpeaking: setSpeaking,
    });
    voiceRef.current = voice;
    postTranscript("system", "Live session started").catch(() => {});
    await voice.start(videoRef.current);
  };

  const end = async () => {
    await voiceRef.current?.stop();
    voiceRef.current = null;
    setSpeaking(false);
    setMuted(false);
  };

  const toggleMute = () => {
    const m = !muted;
    setMuted(m);
    if (voiceRef.current) voiceRef.current.muted = m;
  };

  const choosePatient = (id: string) => {
    const p = patients.find((x) => x.id === id);
    if (!p) return;
    setPatient(p);
    voiceRef.current?.sendText(
      `[CONTEXT] The clinician switched to patient ${p.demo_identifier}. Acknowledge in a few words.`
    );
  };

  const active = status === "live" || status === "connecting" || status === "reconnecting";
  const cards = run?.result?.final_cards ?? [];

  return (
    <main className="mx-auto flex min-h-[calc(100dvh-2rem)] max-w-md flex-col gap-4 px-4 pb-8 pt-5">
      <header className="flex items-end justify-between">
        <div>
          <h1 className="font-[family-name:var(--font-display)] text-lg font-bold uppercase tracking-tight text-stone-900">
            LOUPEIN <span className="text-teal-800">Live</span>
          </h1>
          <p className="text-[11px] italic text-stone-500">Hands-free. Results appear on the laptop.</p>
        </div>
        <span
          className={
            "flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.15em] " +
            (status === "live"
              ? "bg-teal-800 text-white"
              : status === "error"
                ? "bg-red-100 text-red-800"
                : "bg-stone-200 text-stone-600")
          }
        >
          {status === "live" && <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-red-400" />}
          {STATUS_LABEL[status]}
        </span>
      </header>

      <label className="flex items-center gap-3 text-xs uppercase tracking-[0.15em] text-stone-500">
        Patient
        <select
          value={patient?.id ?? ""}
          onChange={(e) => choosePatient(e.target.value)}
          className="flex-1 rounded-md border border-stone-300 bg-white px-3 py-2 font-mono text-sm normal-case tracking-normal text-stone-800"
        >
          {patients.map((p) => (
            <option key={p.id} value={p.id}>
              {p.demo_identifier} — {p.display_name}
            </option>
          ))}
        </select>
      </label>

      <div className="relative aspect-[4/3] overflow-hidden rounded-xl bg-stone-900">
        <video ref={videoRef} muted playsInline autoPlay className="h-full w-full object-cover" />
        {!active && (
          <div className="absolute inset-0 flex items-center justify-center p-6 text-center text-sm text-stone-400">
            Camera and mic start when you go live.
          </div>
        )}
        {speaking && (
          <span className="absolute bottom-3 left-3 rounded-full bg-teal-700/90 px-3 py-1 text-[11px] font-medium text-white">
            Loupes is speaking…
          </span>
        )}
        {muted && active && (
          <span className="absolute right-3 top-3 rounded-full bg-amber-500/90 px-3 py-1 text-[11px] font-medium text-white">
            Mic muted
          </span>
        )}
      </div>

      {detail && (
        <p className="rounded-md border border-stone-300 bg-white px-3 py-2 text-xs text-stone-600">{detail}</p>
      )}

      <div className="flex gap-3">
        {!active ? (
          <button
            onClick={goLive}
            disabled={!patient}
            className="flex-1 rounded-md bg-teal-800 py-3.5 font-[family-name:var(--font-display)] text-sm font-semibold uppercase tracking-[0.15em] text-white transition-colors hover:bg-teal-700 disabled:opacity-40"
          >
            Go live
          </button>
        ) : (
          <>
            <button
              onClick={toggleMute}
              className="rounded-md border border-stone-300 bg-white px-4 py-3.5 text-xs font-semibold uppercase tracking-wider text-stone-700"
            >
              {muted ? "Unmute" : "Mute"}
            </button>
            <button
              onClick={end}
              className="flex-1 rounded-md bg-stone-800 py-3.5 font-[family-name:var(--font-display)] text-sm font-semibold uppercase tracking-[0.15em] text-white hover:bg-stone-700"
            >
              End
            </button>
          </>
        )}
      </div>

      {run && (
        <section className="rounded-lg border border-stone-200 bg-white p-4">
          <p className="text-[10px] font-medium uppercase tracking-[0.2em] text-stone-400">Guardian</p>
          <p className="mt-1 text-sm text-stone-800">
            {run.procedure.replace(/_/g, " ")}
            {run.tooth != null && ` — tooth #${run.tooth}`}
            {" · "}
            {run.state === "running" && <span className="animate-pulse text-teal-700">reviewing the record…</span>}
            {run.state === "failed" && <span className="text-stone-500">could not complete</span>}
            {run.state === "done" &&
              (cards.length ? (
                <span className="font-medium text-amber-700">
                  {cards.length} item{cards.length === 1 ? "" : "s"} to review
                </span>
              ) : (
                <span className="text-teal-800">nothing needs attention</span>
              ))}
          </p>
          {cards.length > 0 && (
            <ul className="mt-2 space-y-1 text-xs text-stone-600">
              {cards.map((c, i) => (
                <li key={i}>
                  <span className={c.decision === "SURFACE" ? "text-amber-700" : "text-stone-500"}>●</span>{" "}
                  {c.title}
                </li>
              ))}
            </ul>
          )}
        </section>
      )}

      <section className="flex-1 space-y-2">
        {lines.length === 0 ? (
          <p className="text-xs leading-relaxed text-stone-400">
            Try: <em>&ldquo;Loupes, I&apos;m about to do an extraction on thirty.&rdquo;</em> Then ask
            follow-ups like <em>&ldquo;what&apos;s the source for that?&rdquo;</em> Use headphones or low
            volume so the mic doesn&apos;t hear the reply.
          </p>
        ) : (
          lines.map((l, i) => (
            <p key={i} className={"text-sm " + (l.role === "dentist" ? "text-stone-500" : "text-stone-900")}>
              <span className="mr-1.5 text-[9px] font-semibold uppercase tracking-[0.15em] text-teal-700">
                {l.role === "dentist" ? "You" : "Loupes"}
              </span>
              {l.text}
            </p>
          ))
        )}
      </section>
    </main>
  );
}
