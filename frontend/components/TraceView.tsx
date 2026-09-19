"use client";

import { useEffect, useRef, useState } from "react";
import type { TraceEvent } from "@/lib/api";

const AGENT_LABELS: Record<string, string> = {
  context_interpreter: "Context",
  guardian: "Guardian",
  skeptic: "Skeptic",
  composer: "Composer",
};

export default function TraceView({
  trace,
  onDone,
}: {
  trace: TraceEvent[] | null; // null while the investigation is still running
  onDone: () => void;
}) {
  const [shown, setShown] = useState(0);
  const endRef = useRef<HTMLDivElement>(null);
  const doneRef = useRef(onDone);
  doneRef.current = onDone;

  useEffect(() => {
    if (!trace) return;
    if (shown >= trace.length) {
      const t = setTimeout(() => doneRef.current(), 700);
      return () => clearTimeout(t);
    }
    const t = setTimeout(() => setShown((s) => s + 1), 350);
    return () => clearTimeout(t);
  }, [trace, shown]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [shown]);

  return (
    <section aria-live="polite">
      <h2 className="mb-6 font-[family-name:var(--font-display)] text-2xl font-semibold uppercase tracking-tight text-stone-900">
        Challenging procedure
        <span className="animate-pulse text-teal-700">…</span>
      </h2>
      <div className="space-y-3 rounded-lg border border-stone-200 bg-stone-900 p-4 font-mono text-[13px] leading-relaxed text-stone-200">
        {!trace && (
          <p className="animate-pulse text-stone-400">
            → Agent reviewing the record…
          </p>
        )}
        {trace?.slice(0, shown).map((ev, i) => {
          const active = i === shown - 1 && shown < trace.length;
          return (
            <div key={ev.sequence_no} className="trace-in">
              <span className="block text-[10px] uppercase tracking-[0.2em] text-teal-500">
                {AGENT_LABELS[ev.agent] ?? ev.agent}
              </span>
              <span className={active ? "text-white" : "text-stone-300"}>
                {active ? "→" : "✓"} {ev.summary}
              </span>
            </div>
          );
        })}
        <div ref={endRef} />
      </div>
    </section>
  );
}
