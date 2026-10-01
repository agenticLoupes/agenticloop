"use client";

import { useEffect, useRef, useState } from "react";
import { askAboutCase, type ChatTurn } from "@/lib/api";

const STARTERS = [
  "What is on file that I should understand for this case?",
  "Why did Guardian surface or stay silent?",
  "Any visit conversation that contradicts the chart?",
  "What medications and allergies are recorded?",
];

type SpeechRec = {
  lang: string;
  interimResults: boolean;
  continuous: boolean;
  onresult: ((ev: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void) | null;
  onerror: (() => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
};

function getSpeechRecognition(): (new () => SpeechRec) | null {
  if (typeof window === "undefined") return null;
  const w = window as Window & {
    SpeechRecognition?: new () => SpeechRec;
    webkitSpeechRecognition?: new () => SpeechRec;
  };
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null;
}

export default function CaseChat({ runId }: { runId: string }) {
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [listening, setListening] = useState(false);
  const [voiceOk, setVoiceOk] = useState(false);
  const recRef = useRef<SpeechRec | null>(null);
  const busyRef = useRef(false);
  const abortRef = useRef<AbortController | null>(null);
  const scroller = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setVoiceOk(getSpeechRecognition() != null);
    return () => {
      recRef.current?.stop();
      recRef.current = null;
      abortRef.current?.abort();
      if (typeof window !== "undefined") window.speechSynthesis?.cancel();
    };
  }, []);

  useEffect(() => {
    const reduce =
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    scroller.current?.scrollTo({
      top: scroller.current.scrollHeight,
      behavior: reduce ? "auto" : "smooth",
    });
  }, [turns, busy]);

  const send = async (text: string) => {
    const question = text.trim();
    if (!question || busyRef.current) return;
    busyRef.current = true;
    const prior = turns;
    const next = [...prior, { role: "dentist" as const, content: question }];
    setTurns(next);
    setDraft("");
    setBusy(true);
    setError(null);
    abortRef.current?.abort();
    const ac = new AbortController();
    abortRef.current = ac;
    try {
      const { answer } = await askAboutCase(runId, question, prior, {
        signal: ac.signal,
      });
      setTurns([...next, { role: "assistant", content: answer }]);
    } catch (err) {
      if ((err as Error).name === "AbortError") return;
      setError("Couldn't answer that just now — the review above is unaffected. Try again.");
    } finally {
      busyRef.current = false;
      setBusy(false);
    }
  };

  const toggleListen = () => {
    if (listening) {
      recRef.current?.stop();
      setListening(false);
      return;
    }
    const Ctor = getSpeechRecognition();
    if (!Ctor) return;
    const rec = new Ctor();
    rec.lang = "en-US";
    rec.interimResults = false;
    rec.continuous = false;
    rec.onresult = (ev) => {
      const said = ev.results[0]?.[0]?.transcript ?? "";
      if (said) setDraft((d) => (d.trim() ? `${d.trim()} ${said}` : said));
    };
    rec.onerror = () => {
      setListening(false);
      setError("We couldn't reach your microphone. Type the question instead.");
    };
    rec.onend = () => setListening(false);
    recRef.current = rec;
    rec.start();
    setListening(true);
  };

  const speak = (text: string) => {
    if (typeof window === "undefined" || !window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.rate = 1;
    window.speechSynthesis.speak(u);
  };

  return (
    <section className="mt-8 rounded-xl border border-stone-200 bg-white shadow-sm">
      <div className="border-b border-stone-100 px-4 py-3">
        <h3 className="text-lg font-semibold text-stone-900">
          Ask about this case
        </h3>
        <p className="mt-1 text-sm leading-relaxed text-stone-600">
          Chat or speak to review what is on file and what Guardian found. Explains
          the record — never tells you what treatment to do.
          {voiceOk && (
            <> Voice uses your browser&apos;s speech service (not stored here).</>
          )}
        </p>
      </div>

      {turns.length === 0 && (
        <div className="flex flex-wrap gap-2 px-4 pt-3">
          {STARTERS.map((q) => (
            <button
              key={q}
              type="button"
              disabled={busy}
              onClick={() => send(q)}
              className="min-h-11 rounded-lg border border-stone-300 px-3 py-2 text-left text-sm leading-snug text-stone-700 hover:border-teal-600 hover:bg-teal-50 hover:text-teal-800 disabled:opacity-40"
            >
              {q}
            </button>
          ))}
        </div>
      )}

      <div
        ref={scroller}
        role="log"
        aria-live="polite"
        aria-relevant="additions"
        aria-busy={busy}
        className="max-h-72 space-y-2.5 overflow-y-auto px-4 py-3"
      >
        {turns.map((t, i) => (
          <div
            key={`${t.role}-${i}-${t.content.slice(0, 24)}`}
            className={t.role === "dentist" ? "ml-6 text-right" : "mr-6"}
          >
            <p className="text-xs font-medium text-stone-500">
              {t.role === "dentist" ? "You" : "Guardian"}
            </p>
            <p
              className={`mt-0.5 inline-block rounded-md px-3 py-2 text-left text-sm leading-relaxed ${
                t.role === "dentist"
                  ? "bg-teal-800 text-white"
                  : "bg-stone-100 text-stone-700"
              }`}
            >
              {t.content}
            </p>
            {t.role === "assistant" && (
              <button
                type="button"
                onClick={() => speak(t.content)}
                className="mt-1 block text-sm font-medium text-teal-800 underline underline-offset-2 hover:text-teal-700"
              >
                Listen
              </button>
            )}
          </div>
        ))}
        {busy && (
          <p className="animate-pulse text-sm text-stone-500">Looking through the case…</p>
        )}
        {error && (
          <p role="alert" className="text-sm text-stone-600">
            {error}
          </p>
        )}
      </div>

      <form
        className="flex items-end gap-2 border-t border-stone-100 p-3"
        onSubmit={(e) => {
          e.preventDefault();
          send(draft);
        }}
      >
        <label className="sr-only" htmlFor="case-chat-input">
          Question about this case
        </label>
        <textarea
          id="case-chat-input"
          name="case-question"
          rows={3}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="e.g. Why was this record shown?"
          className="min-h-[56px] flex-1 resize-none rounded-lg border border-stone-300 bg-white px-3 py-2.5 text-[15px] leading-snug text-stone-900 placeholder:text-stone-500 focus:border-teal-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-800"
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              send(draft);
            }
          }}
        />
        {voiceOk && (
          <button
            type="button"
            onClick={toggleListen}
            aria-pressed={listening}
            aria-label={listening ? "Stop listening" : "Speak a question"}
            className={`h-11 w-11 shrink-0 rounded-lg border text-sm ${
              listening
                ? "border-amber-400 bg-amber-50 text-amber-800"
                : "border-stone-300 text-stone-600 hover:border-teal-700 hover:text-teal-800"
            }`}
          >
            {listening ? (
              <span aria-hidden className="text-lg leading-none">
                ●
              </span>
            ) : (
              <svg
                aria-hidden
                viewBox="0 0 24 24"
                className="mx-auto h-5 w-5"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.75"
              >
                <rect x="9" y="3" width="6" height="11" rx="3" />
                <path d="M6 11a6 6 0 0 0 12 0M12 17v4M9 21h6" />
              </svg>
            )}
          </button>
        )}
        <button
          type="submit"
          disabled={busy || !draft.trim()}
          className="h-11 shrink-0 rounded-lg bg-teal-800 px-4 text-sm font-semibold text-white hover:bg-teal-700 disabled:opacity-40"
        >
          Ask
        </button>
      </form>
    </section>
  );
}
