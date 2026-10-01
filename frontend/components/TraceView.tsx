"use client";

import { useEffect, useRef, useState } from "react";
import type { TraceEvent } from "@/lib/api";

// Plain-English stage names — the dentist should not have to decode agent names.
const AGENT_LABELS: Record<string, string> = {
  context_interpreter: "Understanding the plan",
  guardian: "Reading the record",
  skeptic: "Double-checking findings",
  composer: "Writing it up",
};

export default function TraceView({
  trace,
  complete,
  onDone,
}: {
  trace: TraceEvent[] | null; // grows live while the investigation runs (polled)
  complete: boolean; // true once the run has finished server-side
  onDone: () => void;
}) {
  const [shown, setShown] = useState(0);
  const endRef = useRef<HTMLLIElement>(null);
  const doneRef = useRef(onDone);
  doneRef.current = onDone;

  useEffect(() => {
    if (!trace) return;
    if (shown >= trace.length) {
      // caught up: if the run is over, reveal results; otherwise wait for more lines
      if (complete) {
        const t = setTimeout(() => doneRef.current(), 700);
        return () => clearTimeout(t);
      }
      return;
    }
    const t = setTimeout(() => setShown((s) => s + 1), 350);
    return () => clearTimeout(t);
  }, [trace, shown, complete]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [shown]);

  const visible = trace?.slice(0, shown) ?? [];

  return (
    <section aria-live="polite">
      <h2 className="flex items-center gap-2.5 text-2xl font-semibold text-stone-900">
        <span
          aria-hidden
          className="h-2.5 w-2.5 shrink-0 animate-pulse rounded-full bg-teal-600"
        />
        Checking the record…
      </h2>
      <p className="mt-1.5 text-sm text-stone-600">
        Guardian is going through medications, allergies, notes and imaging. This
        usually takes about 30 seconds.
      </p>

      <ol className="mt-5 space-y-3 rounded-xl border border-stone-200 bg-white p-4 shadow-sm">
        {visible.length === 0 && (
          <li className="flex items-center gap-3 text-sm text-stone-500">
            <span
              aria-hidden
              className="h-5 w-5 shrink-0 animate-pulse rounded-full bg-stone-200"
            />
            Opening the patient&apos;s record…
          </li>
        )}
        {visible.map((ev, i) => {
          const active = i === shown - 1 && (shown < (trace?.length ?? 0) || !complete);
          const stage = AGENT_LABELS[ev.agent] ?? ev.agent;
          const newStage = i === 0 || visible[i - 1].agent !== ev.agent;
          return (
            <li key={ev.sequence_no} className="trace-in flex items-start gap-3">
              <span
                aria-hidden
                className={
                  "mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[11px] font-bold " +
                  (active
                    ? "animate-pulse bg-teal-100 text-teal-800"
                    : "bg-teal-700 text-white")
                }
              >
                {active ? "•" : "✓"}
              </span>
              <span className="min-w-0">
                {newStage && (
                  <span className="block text-xs font-medium text-stone-500">
                    {stage}
                  </span>
                )}
                <span
                  className={
                    "block text-[15px] leading-snug " +
                    (active ? "font-medium text-stone-900" : "text-stone-700")
                  }
                >
                  {ev.summary}
                </span>
              </span>
            </li>
          );
        })}
        <li ref={endRef} />
      </ol>

      <p className="mt-3 text-sm text-stone-500">
        {visible.length > 0
          ? `${visible.length} check${visible.length === 1 ? "" : "s"} done so far.`
          : "Nothing is decided until every source has been read."}
      </p>
    </section>
  );
}
