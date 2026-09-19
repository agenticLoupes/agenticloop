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

// Universal Numbering: upper arch left→right = #1..#16, lower arch left→right = #32..#17
function archPositions(cy: number, flip: boolean) {
  return Array.from({ length: 16 }, (_, i) => {
    const t = ((180 - i * 12) * Math.PI) / 180; // 180° → 0° across 16 teeth
    const x = 160 + 138 * Math.cos(t);
    const y = flip ? cy + 74 * Math.sin(t) : cy - 74 * Math.sin(t);
    return { x, y };
  });
}

function ToothChart({
  selected,
  onSelect,
}: {
  selected: number;
  onSelect: (n: number) => void;
}) {
  const upper = archPositions(96, false); // teeth 1..16
  const lower = archPositions(128, true); // teeth 32..17
  const teeth = [
    ...upper.map((p, i) => ({ ...p, n: i + 1 })),
    ...lower.map((p, i) => ({ ...p, n: 32 - i })),
  ];
  return (
    <svg
      viewBox="0 0 320 226"
      className="w-full select-none"
      role="group"
      aria-label="Tooth chart — choose a tooth"
    >
      <text x="160" y="106" textAnchor="middle" className="fill-stone-400" fontSize="10">
        Upper
      </text>
      <text x="160" y="124" textAnchor="middle" className="fill-stone-400" fontSize="10">
        Lower
      </text>
      {teeth.map(({ x, y, n }) => {
        const active = n === selected;
        return (
          <g
            key={n}
            onClick={() => onSelect(n)}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                onSelect(n);
              }
            }}
            tabIndex={0}
            className="cursor-pointer focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-700"
            role="button"
            aria-pressed={active}
            aria-label={`Tooth ${n}`}
          >
            {/* generous invisible hit area for touch */}
            <circle cx={x} cy={y} r={13} fill="transparent" />
            <circle
              cx={x}
              cy={y}
              r={10}
              className={
                active
                  ? "fill-teal-700 stroke-teal-800"
                  : "fill-white stroke-stone-300 hover:stroke-teal-600"
              }
              strokeWidth={1}
            />
            <text
              x={x}
              y={y + 3}
              textAnchor="middle"
              fontSize="8.5"
              className={active ? "fill-white font-bold" : "fill-stone-600"}
            >
              {n}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

export default function ProcedureForm({
  patientLabel,
  initialProcedure,
  initialTooth,
  onSubmit,
  onBack,
}: {
  patientLabel: string;
  initialProcedure?: string;
  initialTooth?: number;
  onSubmit: (procedure: string, toothNumber: number | null, upload: File | null) => void;
  onBack: () => void;
}) {
  const [procedure, setProcedure] = useState(initialProcedure ?? "extraction");
  const [tooth, setTooth] = useState(initialTooth ?? 30);
  const [upload, setUpload] = useState<File | null>(null);
  const needsTooth = TOOTH_REQUIRED.has(procedure);
  const label = PROCEDURES.find((p) => p.value === procedure)?.label;

  return (
    <section>
      <button
        onClick={onBack}
        className="mb-4 inline-flex min-h-11 items-center gap-1.5 text-sm font-medium text-stone-600 hover:text-teal-800"
      >
        <span aria-hidden>←</span> {patientLabel}
      </button>
      <h2 className="text-2xl font-semibold text-stone-900">
        What are you about to do?
      </h2>
      <p className="mt-1.5 text-sm text-stone-600">
        {initialProcedure
          ? "We've pre-filled this demo case — change anything you like."
          : "Tell Guardian the plan so it knows what to look for."}
      </p>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          onSubmit(procedure, needsTooth ? tooth : null, upload);
        }}
        className="mt-6 space-y-6"
      >
        <fieldset>
          <legend className="mb-2 text-base font-semibold text-stone-900">
            Procedure
          </legend>
          <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-3">
            {PROCEDURES.map((p) => {
              const active = p.value === procedure;
              return (
                <button
                  key={p.value}
                  type="button"
                  onClick={() => setProcedure(p.value)}
                  aria-pressed={active}
                  className={
                    "min-h-11 rounded-lg border px-3 text-sm font-medium transition-colors " +
                    (active
                      ? "border-teal-700 bg-teal-700 text-white"
                      : "border-stone-300 bg-white text-stone-700 hover:border-teal-600 hover:bg-teal-50")
                  }
                >
                  {p.label}
                </button>
              );
            })}
          </div>
        </fieldset>

        {needsTooth && (
          <div>
            <div className="mb-2 flex flex-wrap items-baseline justify-between gap-x-3">
              <span className="text-base font-semibold text-stone-900">Which tooth?</span>
              <span className="text-sm text-stone-600">
                Selected: <strong className="text-teal-800">#{tooth}</strong>
              </span>
            </div>
            <div className="rounded-xl border border-stone-200 bg-white px-2 py-3 shadow-sm">
              <ToothChart selected={tooth} onSelect={setTooth} />
            </div>
            <p className="mt-1.5 text-sm text-stone-500">
              Tap a tooth on the chart (standard #1–#32 numbering).
            </p>
          </div>
        )}

        <div>
          <span className="mb-2 block text-base font-semibold text-stone-900">
            Radiograph{" "}
            <span className="font-normal text-stone-500">(optional)</span>
          </span>
          <label className="flex min-h-14 cursor-pointer items-center justify-between gap-3 rounded-xl border border-dashed border-stone-300 bg-white px-4 py-3 text-sm text-stone-700 hover:border-teal-600 hover:bg-teal-50">
            <span className="min-w-0 truncate">
              {upload ? upload.name : "Attach a sample image (PNG or JPEG)"}
            </span>
            <span className="shrink-0 text-sm font-semibold text-teal-800">
              {upload ? "Change" : "Browse"}
            </span>
            <input
              type="file"
              accept="image/png,image/jpeg"
              className="hidden"
              onChange={(e) => setUpload(e.target.files?.[0] ?? null)}
            />
          </label>
          <p className="mt-1.5 text-sm leading-snug text-stone-500">
            Sample images only — never real patient data. Anything you upload has
            no verified source, so Guardian always asks you to review it.
          </p>
        </div>

        {/* selection summary — the intent in one sentence */}
        <p className="rounded-xl bg-stone-100 px-4 py-3 text-center text-[15px] text-stone-800">
          Checking <strong>{patientLabel}</strong> before{" "}
          <strong>{label?.toLowerCase()}</strong>
          {needsTooth && (
            <>
              {" on tooth "}
              <strong className="text-teal-800">#{tooth}</strong>
            </>
          )}
        </p>

        <div>
          <button
            type="submit"
            className="min-h-14 w-full rounded-xl bg-teal-800 px-5 text-base font-semibold text-white transition-colors hover:bg-teal-700"
          >
            Check the record
          </button>
          <p className="mt-2 text-center text-sm text-stone-500">
            Usually takes about 30 seconds.
          </p>
        </div>
      </form>
    </section>
  );
}
