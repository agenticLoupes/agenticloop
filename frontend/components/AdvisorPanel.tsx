"use client";

import { useState } from "react";
import { askAdvisor, type AdvisorAnswer } from "@/lib/api";

/**
 * The asked surface: the dentist types a clinical question and the Advisor answers it from
 * this patient's records plus published evidence. Every approach shows its citation and
 * every patient fact links to its source record — an answer with neither is not shown as one.
 */
export default function AdvisorPanel({
  patientId,
  procedure,
  toothNumber,
  onViewSource,
}: {
  patientId: string | null;
  procedure: string | null;
  toothNumber: number | null;
  onViewSource: (evidenceId: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const [question, setQuestion] = useState("");
  const [asking, setAsking] = useState(false);
  const [turns, setTurns] = useState<{ question: string; answer: AdvisorAnswer }[]>([]);
  const [failed, setFailed] = useState(false);

  const intent = procedure?.replace("_", " ") ?? "this case";
  const suggestions = [
    `What approaches are documented for ${intent}?`,
    "What does this patient's record change about the usual approach?",
    "What should I discuss with the patient before starting?",
  ];

  const ask = async (q: string) => {
    const text = q.trim();
    if (!text || asking) return;
    setAsking(true);
    setFailed(false);
    setQuestion("");
    try {
      const answer = await askAdvisor({
        question: text,
        patient_id: patientId,
        procedure,
        tooth_number: toothNumber,
        history: turns.flatMap((t) => [
          { role: "user", content: t.question },
          { role: "assistant", content: t.answer.question_focus || t.answer.notes },
        ]),
      });
      if (answer.status === "error") {
        setFailed(true);
      } else {
        setTurns((prev) => [...prev, { question: text, answer }]);
      }
    } catch {
      setFailed(true);
    } finally {
      setAsking(false);
    }
  };

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="mt-6 w-full rounded-lg border border-teal-700 bg-teal-800 py-3 text-xs font-semibold uppercase tracking-[0.15em] text-white transition-colors hover:bg-teal-700"
      >
        Ask about approaches
      </button>
    );
  }

  return (
    <section className="mt-6 rounded-lg border border-stone-200 bg-white p-4">
      <h3 className="font-[family-name:var(--font-display)] text-lg font-medium text-stone-900">
        Ask the advisor
      </h3>
      <p className="mt-1 text-xs leading-relaxed text-stone-500">
        Retrieves this patient&apos;s records and published evidence, and cites both. It
        presents documented options — it does not decide, diagnose, or prescribe.
      </p>

      <div className="mt-4 space-y-5">
        {turns.map((turn, i) => (
          <AdvisorTurn key={i} turn={turn} onViewSource={onViewSource} />
        ))}
      </div>

      {turns.length === 0 && !asking && (
        <div className="mt-4 flex flex-wrap gap-2">
          {suggestions.map((s) => (
            <button
              key={s}
              onClick={() => ask(s)}
              className="rounded-md border border-stone-300 px-3 py-1.5 text-left text-[11px] text-stone-600 transition-colors hover:border-teal-600 hover:text-teal-800"
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {asking && (
        <p className="mt-4 text-xs uppercase tracking-[0.2em] text-teal-800">
          Retrieving records and evidence…
        </p>
      )}

      {failed && (
        <p className="mt-4 rounded-md border border-stone-300 bg-stone-50 p-3 text-xs text-stone-600">
          The advisor could not complete that question. No answer was invented — you can ask
          again.
        </p>
      )}

      <form
        onSubmit={(e) => {
          e.preventDefault();
          ask(question);
        }}
        className="mt-4"
      >
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              ask(question);
            }
          }}
          rows={2}
          placeholder="Ask about approaches or treatment for this case…"
          className="w-full resize-none rounded-md border border-stone-300 p-3 text-sm text-stone-800 placeholder:text-stone-400 focus:border-teal-700 focus:outline-none"
        />
        <button
          type="submit"
          disabled={asking || !question.trim()}
          className="mt-2 w-full rounded-md bg-teal-800 py-2.5 text-xs font-semibold uppercase tracking-[0.15em] text-white transition-colors hover:bg-teal-700 disabled:bg-stone-300"
        >
          {asking ? "Asking…" : "Ask"}
        </button>
      </form>
    </section>
  );
}

function AdvisorTurn({
  turn,
  onViewSource,
}: {
  turn: { question: string; answer: AdvisorAnswer };
  onViewSource: (evidenceId: string) => void;
}) {
  const a = turn.answer;
  const nothingStructured =
    a.approaches.length === 0 && a.patient_context.length === 0 && a.cautions.length === 0;

  return (
    <div className="border-t border-stone-100 pt-4 first:border-0 first:pt-0">
      <p className="text-sm font-medium text-stone-900">{turn.question}</p>

      {a.urgent_referral && (
        <p className="mt-2 rounded-md bg-amber-100 px-3 py-2 text-xs font-medium text-amber-900">
          A retrieved source describes this situation as needing immediate care.
        </p>
      )}

      {a.patient_context.length > 0 && (
        <div className="mt-3">
          <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-stone-400">
            From this patient&apos;s record
          </p>
          {a.patient_context.map((c, i) => (
            <div key={i} className="mt-1.5">
              <p className="text-sm leading-relaxed text-stone-700">{c.finding}</p>
              <div className="mt-1 flex flex-wrap gap-1.5">
                {c.evidence_ids.map((id) => (
                  <button
                    key={id}
                    onClick={() => onViewSource(id)}
                    className="rounded-md border border-stone-300 px-2 py-1 font-mono text-[10px] uppercase tracking-wider text-stone-600 transition-colors hover:border-teal-600 hover:text-teal-800"
                  >
                    {id}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {a.approaches.map((ap, i) => (
        <article key={i} className="mt-3 rounded-md border border-stone-200 p-3">
          <h4 className="text-sm font-medium text-stone-900">{ap.approach}</h4>
          {ap.rationale && (
            <p className="mt-1 text-sm leading-relaxed text-stone-600">{ap.rationale}</p>
          )}
          {ap.patient_specific_considerations.length > 0 && (
            <ul className="mt-2 space-y-1">
              {ap.patient_specific_considerations.map((c, j) => (
                <li key={j} className="text-xs leading-relaxed text-stone-600">
                  · {c}
                </li>
              ))}
            </ul>
          )}
          <p className="mt-2 font-mono text-[10px] uppercase tracking-wider text-stone-400">
            {ap.citations.join(" · ")}
          </p>
        </article>
      ))}

      {a.cautions.length > 0 && (
        <div className="mt-3">
          <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-stone-400">
            Open questions
          </p>
          <ul className="mt-1 space-y-1">
            {a.cautions.map((c, i) => (
              <li key={i} className="text-xs leading-relaxed text-stone-600">
                · {c}
              </li>
            ))}
          </ul>
        </div>
      )}

      {a.patient_communication && (
        <div className="mt-3 rounded-md bg-stone-50 p-3">
          <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-stone-400">
            Explaining it to the patient
          </p>
          <p className="mt-1 text-sm leading-relaxed text-stone-700">
            {a.patient_communication}
          </p>
        </div>
      )}

      {a.notes && (
        <p className="mt-3 whitespace-pre-line text-sm leading-relaxed text-stone-600">
          {a.notes}
        </p>
      )}

      {nothingStructured && !a.notes && (
        <p className="mt-3 text-sm text-stone-600">
          The retrieved sources did not establish an answer to that question.
        </p>
      )}

      {a.citations.length > 0 && (
        <div className="mt-3 border-t border-stone-100 pt-2">
          <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-stone-400">
            Sources
          </p>
          <ul className="mt-1 space-y-1">
            {a.citations.map((c) => (
              <li key={c.citation_id} className="text-xs leading-relaxed">
                {c.url ? (
                  <a
                    href={c.url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-teal-800 underline-offset-2 hover:underline"
                  >
                    {c.citation_id}
                  </a>
                ) : (
                  <span className="text-stone-600">{c.citation_id}</span>
                )}
                {c.label && <span className="text-stone-500"> — {c.label}</span>}
              </li>
            ))}
          </ul>
        </div>
      )}

      {a.unavailable_sources.length > 0 && (
        <p className="mt-2 text-[11px] text-stone-500">
          Source unavailable during this answer: {a.unavailable_sources.join(", ")}.
        </p>
      )}
    </div>
  );
}
