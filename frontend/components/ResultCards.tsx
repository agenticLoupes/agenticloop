"use client";

import { useState } from "react";
import { API_URL, type InvestigationState, type TraceEvent } from "@/lib/api";
import CaseChat from "@/components/CaseChat";

const AGENT_LABELS: Record<string, string> = {
  context_interpreter: "Understanding the plan",
  guardian: "Reading the record",
  skeptic: "Double-checking findings",
  composer: "Writing it up",
};

export default function ResultCards({
  result,
  trace,
  onViewSource,
  onRestart,
  advisor,
}: {
  result: InvestigationState;
  trace: TraceEvent[] | null;
  onViewSource: (evidenceId: string) => void;
  onRestart: () => void;
  advisor?: React.ReactNode;
}) {
  const cards = result.final_cards ?? [];
  const [showTrace, setShowTrace] = useState(false);
  const sourcesChecked =
    trace?.filter((e) => e.agent === "guardian" && e.event_type === "tool_call").length ?? 0;
  const intent =
    `${result.procedure?.replace("_", " ")}` +
    (result.tooth_number != null ? `, tooth #${result.tooth_number}` : "");
  return (
    <section>
      <p className="text-sm text-stone-600">
        <span className="font-medium text-stone-800">{result.patient_id}</span> ·{" "}
        {intent}
      </p>
      <h2 className="mt-1 text-3xl font-semibold text-stone-900">
        Before you begin
      </h2>
      {cards.length > 0 ? (
        <p className="mt-2 inline-flex items-center gap-2 rounded-full bg-amber-100 px-3 py-1 text-sm font-semibold text-amber-900">
          {cards.length} record{cards.length === 1 ? "" : "s"} worth your attention
        </p>
      ) : (
        <div className="mt-4 rounded-xl border border-teal-200 bg-teal-50 p-4">
          <p className="text-base font-semibold text-teal-900">
            Nothing to flag
          </p>
          <p className="mt-1.5 text-sm leading-relaxed text-stone-700">
            Guardian checked {sourcesChecked} source
            {sourcesChecked === 1 ? "" : "s"} for {intent} and found nothing that
            deserves your attention.
            {result.dismissed_count > 0 &&
              ` ${result.dismissed_count} possible finding${
                result.dismissed_count === 1 ? " was" : "s were"
              } ruled out after a second look.`}
          </p>
          <p className="mt-2 text-sm text-stone-600">
            Silence is a result — you only get interrupted when the record says
            something.
          </p>
        </div>
      )}

      {result.summary && (
        <div className="mt-4 rounded-xl border border-stone-200 bg-white p-4 shadow-sm">
          <p className="text-sm font-semibold text-stone-900">
            What Guardian found
          </p>
          <p className="mt-1.5 text-[15px] leading-relaxed text-stone-700">
            {result.summary}
          </p>
        </div>
      )}

      <div className="mt-5 space-y-4">
        {cards.map((card, i) => (
          <article
            key={i}
            className="rounded-xl border border-stone-200 bg-white p-4 shadow-sm"
          >
            <span
              className={`inline-block rounded-full px-3 py-1 text-xs font-semibold ${
                card.decision === "VERIFY"
                  ? "bg-sky-100 text-sky-900"
                  : "bg-amber-100 text-amber-900"
              }`}
            >
              {card.decision === "VERIFY" ? "Worth verifying" : "Please review"}
            </span>
            <h3 className="mt-3 text-lg font-semibold leading-snug text-stone-900">
              {/* the badge above already says "review"/"verify" — drop the repeated prefix */}
              {card.title.replace(/^(Record to review|Item to verify)\s*[—-]\s*/i, "")}
            </h3>
            {card.image_url && (
              <figure className="mt-3">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={`${API_URL}${card.image_url}`}
                  alt={card.image_caption ?? "Synthetic radiograph"}
                  className="w-full rounded-lg border border-stone-200 bg-stone-900"
                />
                {card.image_caption && (
                  <figcaption className="mt-2 text-sm leading-snug text-stone-600">
                    {card.image_caption}
                  </figcaption>
                )}
              </figure>
            )}
            <p className="mt-2 text-[15px] leading-relaxed text-stone-700">
              {card.summary}
            </p>
            <div className="mt-4 rounded-lg bg-stone-50 px-3 py-2.5">
              <p className="text-sm font-semibold text-stone-700">
                Why you&apos;re seeing this
              </p>
              <p className="mt-1 text-sm leading-relaxed text-stone-600">
                {card.reason_shown}
              </p>
            </div>
            {card.evidence_ids.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-2">
                {card.evidence_ids.map((id) => (
                  <button
                    key={id}
                    onClick={() => onViewSource(id)}
                    className="min-h-11 rounded-lg border border-stone-300 px-3.5 text-sm font-medium text-stone-700 transition-colors hover:border-teal-600 hover:bg-teal-50 hover:text-teal-800"
                  >
                    See the source record
                    <span className="ml-1.5 font-mono text-xs text-stone-500">
                      {id}
                    </span>
                  </button>
                ))}
              </div>
            )}
          </article>
        ))}
      </div>

      {trace && trace.length > 0 && (
        <div className="mt-5">
          <button
            onClick={() => setShowTrace((s) => !s)}
            aria-expanded={showTrace}
            className="min-h-11 text-sm font-semibold text-teal-800 underline underline-offset-2 hover:text-teal-700"
          >
            {showTrace
              ? "Hide the steps Guardian took"
              : `Show the ${trace.length} steps Guardian took`}
          </button>
          {showTrace && (
            <ol className="mt-2 space-y-2 rounded-xl border border-stone-200 bg-white p-4 shadow-sm">
              {trace.map((ev) => (
                <li key={ev.sequence_no} className="flex items-start gap-2.5">
                  <span aria-hidden className="mt-1 text-xs text-teal-700">
                    ✓
                  </span>
                  <span>
                    <span className="block text-xs font-medium text-stone-500">
                      {AGENT_LABELS[ev.agent] ?? ev.agent}
                    </span>
                    <span className="block text-sm leading-snug text-stone-700">
                      {ev.summary}
                    </span>
                  </span>
                </li>
              ))}
            </ol>
          )}
        </div>
      )}

      {result.run_id && <CaseChat key={result.run_id} runId={result.run_id} />}

      {advisor}

      <button
        onClick={onRestart}
        className="mt-8 min-h-14 w-full rounded-xl border border-stone-300 bg-white text-base font-semibold text-stone-800 transition-colors hover:border-teal-700 hover:bg-teal-50 hover:text-teal-800"
      >
        Check another patient
      </button>
    </section>
  );
}
