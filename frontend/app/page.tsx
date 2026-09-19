"use client";

import { useCallback, useState } from "react";
import {
  getRun,
  getTrace,
  resetDemo,
  startInvestigation,
  uploadImaging,
  type InvestigationState,
  type Patient,
  type TraceEvent,
} from "@/lib/api";
import PatientSelect, { type ScenarioSuggestion } from "@/components/PatientSelect";
import ProcedureForm from "@/components/ProcedureForm";
import TraceView from "@/components/TraceView";
import ResultCards from "@/components/ResultCards";
import EvidenceModal from "@/components/EvidenceModal";

type Step = "patient" | "procedure" | "investigating" | "results" | "error";

const STEP_LABELS = ["Patient", "Procedure", "Review"] as const;
const STEP_INDEX: Record<Step, number> = {
  patient: 0,
  procedure: 1,
  investigating: 2,
  results: 2,
  error: 2,
};

function Stepper({ current }: { current: number }) {
  return (
    <ol className="mb-8 flex items-center gap-2" aria-label="Progress">
      {STEP_LABELS.map((label, i) => {
        const done = i < current;
        const active = i === current;
        return (
          <li key={label} className="flex flex-1 items-center gap-2">
            <span
              aria-hidden
              className={
                "flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-semibold " +
                (done
                  ? "bg-teal-700 text-white"
                  : active
                    ? "bg-teal-700 text-white"
                    : "border border-stone-300 bg-white text-stone-500")
              }
            >
              {done ? "✓" : i + 1}
            </span>
            <span
              className={
                "truncate text-sm " +
                (active ? "font-semibold text-stone-900" : "text-stone-500")
              }
            >
              {label}
              {active && <span className="sr-only"> (current step)</span>}
            </span>
          </li>
        );
      })}
    </ol>
  );
}

export default function Home() {
  const [step, setStep] = useState<Step>("patient");
  const [patient, setPatient] = useState<Patient | null>(null);
  const [suggested, setSuggested] = useState<ScenarioSuggestion | undefined>();
  const [intent, setIntent] = useState<{
    procedure: string;
    tooth_number: number | null;
  } | null>(null);
  const [result, setResult] = useState<InvestigationState | null>(null);
  const [trace, setTrace] = useState<TraceEvent[] | null>(null);
  const [runComplete, setRunComplete] = useState(false);
  const [evidenceId, setEvidenceId] = useState<string | null>(null);

  const investigate = useCallback(
    async (
      patientId: string,
      procedure: string,
      toothNumber: number | null,
      upload: File | null = null
    ) => {
      setStep("investigating");
      setTrace(null);
      setResult(null);
      setRunComplete(false);
      try {
        if (upload) {
          await uploadImaging(patientId, toothNumber, upload);
        }
        // POST returns run_id immediately; poll the live trace while the agent works
        const { run_id } = await startInvestigation({
          patient_id: patientId,
          procedure,
          tooth_number: toothNumber,
        });
        for (;;) {
          await new Promise((r) => setTimeout(r, 1500));
          const [tr, run] = await Promise.all([getTrace(run_id), getRun(run_id)]);
          setTrace(tr);
          if (run.status === "complete" && run.result) {
            setResult(run.result);
            setRunComplete(true);
            return;
          }
          if (run.status === "error") {
            throw new Error(run.result?.error ?? "run failed");
          }
        }
      } catch {
        setStep("error");
      }
    },
    []
  );

  const restart = () => {
    setStep("patient");
    setPatient(null);
    setIntent(null);
    setResult(null);
    setTrace(null);
  };

  return (
    <main className="mx-auto flex min-h-[calc(100vh-2.5rem)] max-w-lg flex-col px-5 pb-10 pt-7">
      <header className="mb-6">
        <h1 className="font-[family-name:var(--font-display)] text-2xl font-bold uppercase tracking-tight text-stone-900">
          DentAssist <span className="text-teal-800">Guardian</span>
        </h1>
        <p className="mt-1 text-sm text-stone-600">
          A second pair of eyes on the chart before you start.
        </p>
      </header>

      <Stepper current={STEP_INDEX[step]} />

      <div className="flex-1">
        {(step === "results" || step === "error") && (
          <button
            onClick={restart}
            className="mb-4 inline-flex min-h-11 items-center gap-1.5 text-sm font-medium text-stone-600 hover:text-teal-800"
          >
            <span aria-hidden>←</span> Back to all patients
          </button>
        )}
        {step === "patient" && (
          <PatientSelect
            onSelect={(p, s) => {
              setPatient(p);
              setSuggested(s);
              setStep("procedure");
            }}
          />
        )}

        {step === "procedure" && patient && (
          <ProcedureForm
            patientLabel={patient.demo_identifier}
            initialProcedure={suggested?.procedure}
            initialTooth={suggested?.tooth ?? undefined}
            onBack={() => setStep("patient")}
            onSubmit={(procedure, toothNumber, upload) => {
              setIntent({ procedure, tooth_number: toothNumber });
              investigate(patient.id, procedure, toothNumber, upload);
            }}
          />
        )}

        {step === "investigating" && (
          <TraceView
            trace={trace}
            complete={runComplete}
            onDone={() => setStep("results")}
          />
        )}

        {step === "results" && result && (
          <ResultCards
            result={result}
            trace={trace}
            onViewSource={setEvidenceId}
            onRestart={restart}
          />
        )}

        {step === "error" && (
          <section className="rounded-xl border border-stone-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold text-stone-900">
              The check didn&apos;t finish
            </h2>
            <p className="mt-2 text-sm leading-relaxed text-stone-600">
              Something went wrong along the way, so no result was produced —
              nothing was guessed or invented. It&apos;s safe to try again.
            </p>
            <div className="mt-5 flex flex-wrap gap-3">
              {patient && intent && (
                <button
                  onClick={() =>
                    investigate(patient.id, intent.procedure, intent.tooth_number)
                  }
                  className="min-h-11 rounded-lg bg-teal-800 px-5 text-sm font-semibold text-white hover:bg-teal-700"
                >
                  Try again
                </button>
              )}
              <button
                onClick={restart}
                className="min-h-11 rounded-lg border border-stone-300 bg-white px-5 text-sm font-semibold text-stone-700 hover:border-stone-500"
              >
                Start over
              </button>
            </div>
          </section>
        )}
      </div>

      {evidenceId && (
        <EvidenceModal evidenceId={evidenceId} onClose={() => setEvidenceId(null)} />
      )}

      <footer className="mt-10 flex items-center justify-between gap-4 border-t border-stone-200 pt-4 text-sm text-stone-500">
        <span>Prototype — not a medical device.</span>
        <button
          onClick={() => {
            resetDemo().catch(() => {});
            restart();
          }}
          className="min-h-11 font-medium text-stone-600 underline underline-offset-2 hover:text-teal-800"
        >
          Reset demo
        </button>
      </footer>
    </main>
  );
}
