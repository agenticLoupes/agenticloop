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

const STEPS = [
  ["1", "State the intent", "procedure + tooth"],
  ["2", "Guardian investigates", "meds · allergies · notes · imaging"],
  ["3", "Review the evidence", "only source-backed records"],
] as const;

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
      aria-label="Tooth chart — tap a tooth"
    >
      <text x="160" y="108" textAnchor="middle" className="fill-stone-300" fontSize="9" letterSpacing="2">
        UPPER
      </text>
      <text x="160" y="124" textAnchor="middle" className="fill-stone-300" fontSize="9" letterSpacing="2">
        LOWER
      </text>
      {teeth.map(({ x, y, n }) => {
        const active = n === selected;
        return (
          <g
            key={n}
            onClick={() => onSelect(n)}
            className="cursor-pointer"
            role="button"
            aria-label={`Tooth ${n}`}
          >
            {/* generous invisible hit area for touch */}
            <circle cx={x} cy={y} r={13} fill="transparent" />
            <circle
              cx={x}
              cy={y}
              r={9.5}
              className={
                active
                  ? "fill-teal-700 stroke-teal-800"
                  : "fill-white stroke-stone-300 hover:stroke-teal-600"
              }
              strokeWidth={1}
            />
            <text
              x={x}
              y={y + 2.8}
              textAnchor="middle"
              fontSize="7.5"
              className={active ? "fill-white font-bold" : "fill-stone-500"}
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
        className="mb-4 text-xs uppercase tracking-wider text-stone-500 hover:text-stone-800"
      >
        ← {patientLabel}
      </button>
      <h2 className="mb-2 font-[family-name:var(--font-display)] text-2xl font-semibold uppercase tracking-tight text-stone-900">
        What are you about to do?
      </h2>
      {initialProcedure && (
        <p className="mb-4 text-xs text-teal-800">
          Pre-filled with this demo case&apos;s scenario — change anything to
          explore.
        </p>
      )}

      {/* how it works — one-glance explainer */}
      <ol className="mb-6 grid grid-cols-3 gap-2">
        {STEPS.map(([n, title, sub]) => (
          <li key={n} className="rounded-md border border-stone-200 bg-white px-2.5 py-2">
            <span className="block font-mono text-[10px] text-teal-700">{n}</span>
            <span className="block text-[11px] font-semibold leading-tight text-stone-800">
              {title}
            </span>
            <span className="block text-[10px] leading-tight text-stone-400">{sub}</span>
          </li>
        ))}
      </ol>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          onSubmit(procedure, needsTooth ? tooth : null, upload);
        }}
        className="space-y-5"
      >
        <div>
          <span className="mb-2 block text-xs font-medium uppercase tracking-[0.2em] text-stone-500">
            Procedure
          </span>
          <div className="grid grid-cols-3 gap-2">
            {PROCEDURES.map((p) => {
              const active = p.value === procedure;
              return (
                <button
                  key={p.value}
                  type="button"
                  onClick={() => setProcedure(p.value)}
                  aria-pressed={active}
                  className={
                    "rounded-md border px-2 py-2.5 text-xs font-medium transition-colors " +
                    (active
                      ? "border-teal-700 bg-teal-700 text-white"
                      : "border-stone-300 bg-white text-stone-700 hover:border-teal-600")
                  }
                >
                  {p.label}
                </button>
              );
            })}
          </div>
        </div>

        {needsTooth && (
          <div>
            <span className="mb-1 block text-xs font-medium uppercase tracking-[0.2em] text-stone-500">
              Tooth — tap the chart
            </span>
            <div className="rounded-lg border border-stone-200 bg-white px-2 py-3">
              <ToothChart selected={tooth} onSelect={setTooth} />
            </div>
          </div>
        )}

        <div>
          <span className="mb-1 block text-xs font-medium uppercase tracking-[0.2em] text-stone-500">
            Attach radiograph — optional
          </span>
          <label className="flex cursor-pointer items-center justify-between rounded-md border border-dashed border-stone-300 bg-white px-3 py-2.5 text-sm text-stone-600 hover:border-teal-600">
            <span>{upload ? upload.name : "Upload a sample image (PNG/JPEG)"}</span>
            <span className="text-xs font-semibold uppercase tracking-wider text-teal-800">
              {upload ? "Change" : "Browse"}
            </span>
            <input
              type="file"
              accept="image/png,image/jpeg"
              className="hidden"
              onChange={(e) => setUpload(e.target.files?.[0] ?? null)}
            />
          </label>
          <p className="mt-1 text-[10px] leading-snug text-stone-400">
            Sample/synthetic images only — never real patient data. Uploads have no
            verified source, so they always require your review (never auto-surfaced).
          </p>
        </div>

        {/* selection summary — the intent in one sentence */}
        <p className="rounded-md bg-stone-100 px-3 py-2.5 text-center text-sm text-stone-700">
          {label}
          {needsTooth && (
            <>
              {" — tooth "}
              <span className="font-semibold text-teal-800">#{tooth}</span>
            </>
          )}
          {" · "}
          {patientLabel}
        </p>

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
