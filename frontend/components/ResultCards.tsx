"use client";

import { useState } from "react";
import { API_URL, type InvestigationState, type TraceEvent } from "@/lib/api";

export default function ResultCards({
  result,
  trace,
  onViewSource,
  onRestart,
}: {
  result: InvestigationState;
  trace: TraceEvent[] | null;
  onViewSource: (evidenceId: string) => void;
  onRestart: () => void;
}) {
  const cards = result.final_cards ?? [];
  const [showTrace, setShowTrace] = useState(false);
  const sourcesChecked =
    trace?.filter((e) => e.agent === "guardian" && e.event_type === "tool_call").length ?? 0;
  const intent =
    `${result.procedure?.replace("_", " ")}` +
    (result.tooth_number != null ? ` — tooth #${result.tooth_number}` : "");
  return (
    <section>
      <h2 className="font-[family-name:var(--font-display)] text-3xl font-semibold uppercase tracking-tight text-stone-900">
        Before you begin
      </h2>
      {cards.length > 0 ? (
        <p className="mt-1 text-xs font-medium uppercase tracking-[0.2em] text-amber-700">
          {cards.length} record{cards.length === 1 ? "" : "s"} to review
        </p>
      ) : (
        <div className="mt-4 rounded-lg border border-teal-200 bg-teal-50/60 p-4">
          <p className="text-xs font-medium uppercase tracking-[0.2em] text-teal-800">
            Review complete
          </p>
          <p className="mt-1 text-sm text-stone-600">
            Guardian investigated {sourcesChecked} record source
            {sourcesChecked === 1 ? "" : "s"} for <em>{intent}</em> and found
            nothing that deserves your attention.
            {result.dismissed_count > 0 &&
              ` ${result.dismissed_count} candidate record${
                result.dismissed_count === 1 ? "" : "s"
              } dismissed after challenge.`}
          </p>
          <p className="mt-2 text-xs text-stone-500">
            Silence is a result: no interruption when the record holds nothing
            relevant.
          </p>
        </div>
      )}

      {result.summary && (
        <div className="mt-4 rounded-lg border border-stone-200 bg-white p-4">
          <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-stone-400">
            Investigation summary
          </p>
          <p className="mt-1.5 text-sm leading-relaxed text-stone-700">
            {result.summary}
          </p>
        </div>
      )}

      {trace && trace.length > 0 && (
        <div className="mt-4">
          <button
            onClick={() => setShowTrace((s) => !s)}
            className="text-xs font-medium uppercase tracking-[0.15em] text-teal-800 underline-offset-2 hover:underline"
          >
            {showTrace ? "Hide investigation" : "View investigation"}
          </button>
          {showTrace && (
            <div className="mt-2 space-y-1.5 rounded-lg bg-stone-900 p-3 font-mono text-[12px] leading-relaxed text-stone-300">
              {trace.map((ev) => (
                <p key={ev.sequence_no}>
                  <span className="mr-1.5 text-[9px] uppercase tracking-[0.15em] text-teal-500">
                    {ev.agent === "context_interpreter" ? "context" : ev.agent}
                  </span>
                  {ev.summary}
                </p>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="mt-5 space-y-4">
        {cards.map((card, i) => (
          <article
            key={i}
            className="rounded-lg border border-stone-200 bg-white p-4 shadow-sm"
          >
            <span
              className={`inline-block rounded-sm px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.15em] ${
                card.decision === "VERIFY"
                  ? "bg-blue-100 text-blue-800"
                  : "bg-amber-100 text-amber-800"
              }`}
            >
              {card.decision === "VERIFY" ? "Item to verify" : "Record to review"}
            </span>
            <h3 className="mt-2.5 font-[family-name:var(--font-display)] text-lg font-medium text-stone-900">
              {card.title}
            </h3>
            {card.image_url && (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={`${API_URL}${card.image_url}`}
                alt="Synthetic radiograph — tap View source for the full record"
                className="mt-2.5 w-full rounded-md border border-stone-200 bg-stone-900"
              />
            )}
            <p className="mt-1 text-sm leading-relaxed text-stone-600">
              {card.summary}
            </p>
            <div className="mt-3 border-t border-stone-100 pt-3">
              <p className="text-[10px] font-medium uppercase tracking-[0.2em] text-stone-400">
                Why shown?
              </p>
              <p className="mt-1 text-xs text-stone-500">{card.reason_shown}</p>
            </div>
            {card.evidence_ids.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-2">
                {card.evidence_ids.map((id) => (
                  <button
                    key={id}
                    onClick={() => onViewSource(id)}
                    className="rounded-md border border-stone-300 px-3 py-1.5 font-mono text-[11px] uppercase tracking-wider text-stone-700 transition-colors hover:border-teal-600 hover:text-teal-800"
                  >
                    View source · {id}
                  </button>
                ))}
              </div>
            )}
          </article>
        ))}
      </div>

      <button
        onClick={onRestart}
        className="mt-8 w-full rounded-md border border-stone-300 bg-white py-3 text-xs font-semibold uppercase tracking-[0.15em] text-stone-700 transition-colors hover:border-teal-700 hover:text-teal-800"
      >
        Run another check
      </button>
    </section>
  );
}
