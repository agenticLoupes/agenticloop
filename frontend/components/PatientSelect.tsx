"use client";

import { useEffect, useState } from "react";
import { API_URL, getPatients, type Patient } from "@/lib/api";

// What each authored scenario demonstrates (db/scenarios.md) — so testers know where to look.
// suggested = the procedure+tooth that exercises the scenario; pre-filled on selection.
// thumb = the case's radiograph (imaging scenarios show their actual film).
export type ScenarioSuggestion = { procedure: string; tooth: number | null };
const SCENARIO_HINTS: Record<
  string,
  { tag: string; hint: string; suggested: ScenarioSuggestion; thumb?: string }
> = {
  "DEMO-007": { tag: "SURFACE + TRANSCRIPT", hint: "Active Warfarin — and a visit transcript that contradicts it", suggested: { procedure: "extraction", tooth: 30 } },
  "DEMO-008": { tag: "SILENCE", hint: "Stale history only — the agent should stay quiet", suggested: { procedure: "extraction", tooth: 3 } },
  "DEMO-009": { tag: "VERIFY", hint: "A note mentions a medication change; current status unknown", suggested: { procedure: "extraction", tooth: 19 }, thumb: "/assets/imaging/IMG-003_thumb.png" },
  "DEMO-010": { tag: "IMAGING", hint: "Radiograph of the extraction site — vision review", suggested: { procedure: "extraction", tooth: 30 }, thumb: "/assets/imaging/IMG-001_thumb.png" },
  "DEMO-011": { tag: "IMAGING", hint: "Implant candidate — radiograph of the #8 region on file", suggested: { procedure: "implant", tooth: 8 }, thumb: "/assets/imaging/IMG-004_thumb.png" },
  "DEMO-012": { tag: "ALLERGY", hint: "Documented latex sensitivity — relevant to most procedures", suggested: { procedure: "root_canal", tooth: 9 } },
  "DEMO-014": { tag: "ALLERGY", hint: "Documented lidocaine reaction + diabetes", suggested: { procedure: "filling", tooth: 12 } },
  "DEMO-016": { tag: "TRANSCRIPT", hint: "On an anticoagulant; benign visit transcript", suggested: { procedure: "extraction", tooth: 14 } },
  "DEMO-017": { tag: "IMAGING", hint: "Radiograph of the #30 region on file", suggested: { procedure: "crown", tooth: 30 }, thumb: "/assets/imaging/IMG-005_thumb.png" },
};

// scenario-type icon for cases without a film on file (stroke SVGs, clinical style)
function TagIcon({ tag }: { tag: string }) {
  const cls = "h-5 w-5";
  const stroke = { fill: "none", stroke: "currentColor", strokeWidth: 1.6, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
  switch (tag) {
    case "SURFACE + TRANSCRIPT": // pill / medication
      return (
        <svg viewBox="0 0 24 24" className={cls} {...stroke}>
          <rect x="3.5" y="8.5" width="17" height="7" rx="3.5" transform="rotate(-35 12 12)" />
          <line x1="9.4" y1="13.8" x2="14.6" y2="10.2" />
        </svg>
      );
    case "ALLERGY": // alert triangle
      return (
        <svg viewBox="0 0 24 24" className={cls} {...stroke}>
          <path d="M12 4 21 19 H3 Z" />
          <line x1="12" y1="10" x2="12" y2="14" />
          <circle cx="12" cy="16.6" r="0.4" />
        </svg>
      );
    case "TRANSCRIPT": // speech bubble
      return (
        <svg viewBox="0 0 24 24" className={cls} {...stroke}>
          <path d="M4 6 h16 v10 h-9 l-4 3.5 v-3.5 h-3 Z" />
          <line x1="8" y1="10" x2="16" y2="10" />
          <line x1="8" y1="13" x2="13" y2="13" />
        </svg>
      );
    case "VERIFY": // magnifier with ?
      return (
        <svg viewBox="0 0 24 24" className={cls} {...stroke}>
          <circle cx="10.5" cy="10.5" r="6" />
          <line x1="15" y1="15" x2="20" y2="20" />
          <path d="M8.8 9 a1.7 1.7 0 1 1 2.4 1.7 c-0.5 0.25 -0.7 0.55 -0.7 1.1" />
          <circle cx="10.5" cy="13.6" r="0.35" />
        </svg>
      );
    case "SILENCE": // bell, slashed
      return (
        <svg viewBox="0 0 24 24" className={cls} {...stroke}>
          <path d="M8 16 v-5 a4 4 0 0 1 8 0 v5 l1.5 2 h-11 Z" />
          <path d="M10.5 20.5 a1.8 1.8 0 0 0 3 0" />
          <line x1="4.5" y1="4.5" x2="19.5" y2="19.5" />
        </svg>
      );
    case "IMAGING": // radiograph film: frame + tooth silhouettes
      return (
        <svg viewBox="0 0 24 24" className={cls} {...stroke}>
          <rect x="3.5" y="5" width="17" height="14" rx="2" />
          <path d="M7 12 v-1.5 a1.6 1.6 0 0 1 3.2 0 V12 M7.4 12 l0.8 3.4 M9.4 12 l-0.8 3.4" />
          <path d="M13.8 12 v-1.5 a1.6 1.6 0 0 1 3.2 0 V12 M14.2 12 l0.8 3.4 M16.2 12 l-0.8 3.4" />
        </svg>
      );
    default: // record dot
      return (
        <svg viewBox="0 0 24 24" className={cls} {...stroke}>
          <circle cx="12" cy="12" r="3.5" />
        </svg>
      );
  }
}

export default function PatientSelect({
  onSelect,
}: {
  onSelect: (p: Patient, suggested?: ScenarioSuggestion) => void;
}) {
  const [patients, setPatients] = useState<Patient[] | null>(null);
  const [error, setError] = useState(false);
  const [showAll, setShowAll] = useState(false);

  const load = () => {
    setError(false);
    setPatients(null);
    getPatients().then(setPatients, () => setError(true));
  };
  useEffect(load, []);

  return (
    <section>
      <p className="mb-5 rounded-md border border-teal-900/15 bg-teal-50 px-3.5 py-3 text-[13px] leading-relaxed text-teal-950">
        An autonomous agent reviews a patient&apos;s record <em>before</em> a
        procedure — it investigates medications, allergies, notes and imaging,
        challenges its own findings, and surfaces only source-backed records
        worth your review.
      </p>
      <h2 className="mb-4 text-xs font-medium uppercase tracking-[0.2em] text-stone-500">
        Select demo patient
      </h2>
      {error && (
        <div className="rounded-md border border-stone-300 bg-white p-4 text-sm text-stone-600">
          <p>Recoverable demo error — patient list unavailable.</p>
          <button
            onClick={load}
            className="mt-3 rounded-md bg-stone-800 px-4 py-2 text-xs font-medium uppercase tracking-wider text-white hover:bg-stone-700"
          >
            Retry
          </button>
        </div>
      )}
      {!error && !patients && (
        <p className="animate-pulse font-mono text-sm text-stone-400">
          Loading patients…
        </p>
      )}
      {patients && (
        <ul className="divide-y divide-stone-200 overflow-hidden rounded-lg border border-stone-200 bg-white">
          {[...patients]
            .filter((p) => showAll || SCENARIO_HINTS[p.id])
            .sort((a, b) => (SCENARIO_HINTS[b.id] ? 1 : 0) - (SCENARIO_HINTS[a.id] ? 1 : 0))
            .map((p) => {
              const s = SCENARIO_HINTS[p.id];
              return (
                <li key={p.id}>
                  <button
                    onClick={() => onSelect(p, s?.suggested)}
                    className="flex w-full items-center gap-3 px-4 py-3 text-left transition-colors hover:bg-teal-50/60 focus-visible:bg-teal-50/60 focus-visible:outline-none"
                  >
                    {s?.thumb ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        src={`${API_URL}${s.thumb}`}
                        alt=""
                        aria-hidden
                        className="h-12 w-12 shrink-0 rounded-lg border border-teal-200 object-cover shadow-sm"
                      />
                    ) : (
                      <span
                        aria-hidden
                        className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg border border-stone-200 bg-stone-50 text-stone-400"
                      >
                        <TagIcon tag={s?.tag ?? ""} />
                      </span>
                    )}
                    <span className="min-w-0 flex-1">
                      <span className="flex items-center gap-2">
                        <span className="font-mono text-sm font-medium text-stone-800">
                          {p.demo_identifier}
                        </span>
                        {s && (
                          <span className="rounded-sm bg-teal-800/10 px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wider text-teal-800">
                            {s.tag}
                          </span>
                        )}
                      </span>
                      <span className="block text-xs text-stone-500">
                        {s ? s.hint : p.display_name}
                      </span>
                      {s && (
                        <span className="mt-0.5 block text-[10px] uppercase tracking-wider text-stone-400">
                          Try: {s.suggested.procedure.replace("_", " ")}
                          {s.suggested.tooth != null && ` · tooth #${s.suggested.tooth}`}
                        </span>
                      )}
                    </span>
                    <span aria-hidden className="shrink-0 text-teal-700">
                      →
                    </span>
                  </button>
                </li>
              );
            })}
        </ul>
      )}
      {patients && patients.some((p) => !SCENARIO_HINTS[p.id]) && (
        <button
          onClick={() => setShowAll((v) => !v)}
          className="mt-3 w-full text-center text-xs uppercase tracking-wider text-stone-400 underline-offset-2 hover:text-stone-600 hover:underline"
        >
          {showAll
            ? "Hide background patients"
            : `Show ${patients.filter((p) => !SCENARIO_HINTS[p.id]).length} background patients`}
        </button>
      )}
    </section>
  );
}
