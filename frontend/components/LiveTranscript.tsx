"use client";

// Laptop mirror of the phone's spoken conversation (/live). Hidden until a live session
// has said something; each "Live session started" marker starts a fresh panel.

import { useEffect, useState } from "react";
import { getTranscript, type TranscriptLine } from "@/lib/api";

const POLL_MS = 1500;
const SHOWN = 6;

export default function LiveTranscript() {
  const [lines, setLines] = useState<TranscriptLine[]>([]);

  useEffect(() => {
    let since = 0;
    let alive = true;
    const tick = async () => {
      try {
        const fresh = await getTranscript(since);
        if (!alive || !fresh.length) return;
        since = fresh[fresh.length - 1].id;
        setLines((ls) => {
          let next = [...ls, ...fresh];
          const lastStart = next.map((l) => l.role).lastIndexOf("system");
          if (lastStart >= 0) next = next.slice(lastStart + 1);
          return next.slice(-SHOWN);
        });
      } catch {
        /* backend briefly unavailable; next tick retries */
      }
    };
    void tick();
    const t = setInterval(tick, POLL_MS);
    return () => {
      alive = false;
      clearInterval(t);
    };
  }, []);

  if (!lines.length) return null;
  return (
    <section
      aria-live="polite"
      className="mb-6 rounded-lg border border-teal-900/15 bg-teal-50/60 px-3.5 py-3"
    >
      <p className="mb-1.5 flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-[0.2em] text-teal-800">
        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-red-500" />
        Live conversation
      </p>
      <div className="space-y-1">
        {lines.map((l) => (
          <p
            key={l.id}
            className={"trace-in text-[13px] leading-snug " + (l.role === "dentist" ? "text-stone-500" : "text-stone-900")}
          >
            <span className="mr-1.5 text-[9px] font-semibold uppercase tracking-[0.15em] text-teal-700">
              {l.role === "dentist" ? "Dentist" : "Loupes"}
            </span>
            {l.text}
          </p>
        ))}
      </div>
    </section>
  );
}
