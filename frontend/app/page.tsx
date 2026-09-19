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
    <main className="mx-auto flex min-h-[calc(100vh-2rem)] max-w-md flex-col px-5 pb-10 pt-8">
      <header className="mb-8">
        <h1 className="font-[family-name:var(--font-display)] text-xl font-bold uppercase tracking-tight text-stone-900">
          DentAssist{" "}
          <span className="text-teal-800">Guardian</span>
        </h1>
        <p className="mt-0.5 text-xs italic text-stone-500">
          Before you begin, let the record challenge the plan.
        </p>
      </header>

      <div className="flex-1">
        {(step === "results" || step === "error") && (
          <button
            onClick={restart}
            className="mb-4 text-xs uppercase tracking-wider text-stone-500 hover:text-stone-800"
          >
            ← All patients
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
          <section className="rounded-lg border border-stone-300 bg-white p-5">
            <h2 className="text-xs font-semibold uppercase tracking-[0.2em] text-stone-700">
              Recoverable demo error
            </h2>
            <p className="mt-2 text-sm leading-relaxed text-stone-600">
              The investigation could not be completed. No result was invented.
              You can retry the check safely.
            </p>
            <div className="mt-4 flex gap-3">
              {patient && intent && (
                <button
                  onClick={() =>
                    investigate(patient.id, intent.procedure, intent.tooth_number)
                  }
                  className="rounded-md bg-teal-800 px-4 py-2 text-xs font-semibold uppercase tracking-wider text-white hover:bg-teal-700"
                >
                  Retry
                </button>
              )}
              <button
                onClick={restart}
                className="rounded-md border border-stone-300 px-4 py-2 text-xs font-semibold uppercase tracking-wider text-stone-700 hover:border-stone-500"
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

      <footer className="mt-10 flex items-center justify-between border-t border-stone-200 pt-4 text-[10px] uppercase tracking-[0.2em] text-stone-400">
        <span>Synthetic data — prototype</span>
        <button
          onClick={() => {
            resetDemo().catch(() => {});
            restart();
          }}
          className="underline-offset-2 hover:text-stone-600 hover:underline"
        >
          Reset demo
        </button>
      </footer>
    </main>
  );
}
