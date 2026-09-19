"use client";

import { useState } from "react";

const PROCEDURES = [
  { value: "extraction", label: "Extraction" },
  { value: "root_canal", label: "Root canal" },
  { value: "crown", label: "Crown" },
  { value: "filling", label: "Filling" },
  { value: "implant", label: "Implant" },
  { value: "cleaning", label: "Cleaning" },
];

const TOOTH_REQUIRED = new Set([
  "extraction",
  "root_canal",
  "crown",
  "filling",
  "implant",
]);

export default function ProcedureForm({
  patientLabel,
  onSubmit,
  onBack,
}: {
  patientLabel: string;
  onSubmit: (procedure: string, toothNumber: number | null) => void;
  onBack: () => void;
}) {
  const [procedure, setProcedure] = useState("extraction");
  const [tooth, setTooth] = useState("30");
  const needsTooth = TOOTH_REQUIRED.has(procedure);

  return (
    <section>
      <button
        onClick={onBack}
        className="mb-4 text-xs uppercase tracking-wider text-stone-500 hover:text-stone-800"
      >
        ← {patientLabel}
      </button>
      <h2 className="mb-6 font-[family-name:var(--font-display)] text-2xl font-semibold uppercase tracking-tight text-stone-900">
        What are you about to do?
      </h2>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          onSubmit(procedure, needsTooth ? Number(tooth) : null);
        }}
        className="space-y-5"
      >
        <label className="block">
          <span className="mb-1.5 block text-xs font-medium uppercase tracking-[0.2em] text-stone-500">
            Procedure
          </span>
          <select
            value={procedure}
            onChange={(e) => setProcedure(e.target.value)}
            className="w-full rounded-md border border-stone-300 bg-white px-3 py-2.5 text-sm text-stone-800 focus:border-teal-600 focus:outline-none"
          >
            {PROCEDURES.map((p) => (
              <option key={p.value} value={p.value}>
                {p.label}
              </option>
            ))}
          </select>
        </label>
        {needsTooth && (
          <label className="block">
            <span className="mb-1.5 block text-xs font-medium uppercase tracking-[0.2em] text-stone-500">
              Tooth
            </span>
            <select
              value={tooth}
              onChange={(e) => setTooth(e.target.value)}
              className="w-full rounded-md border border-stone-300 bg-white px-3 py-2.5 text-sm text-stone-800 focus:border-teal-600 focus:outline-none"
            >
              {Array.from({ length: 32 }, (_, i) => i + 1).map((n) => (
                <option key={n} value={n}>
                  #{n}
                </option>
              ))}
            </select>
          </label>
        )}
        <button
          type="submit"
          className="w-full rounded-md bg-teal-800 py-3.5 font-[family-name:var(--font-display)] text-sm font-semibold uppercase tracking-[0.15em] text-white transition-colors hover:bg-teal-700"
        >
          Challenge procedure
        </button>
      </form>
    </section>
  );
}
