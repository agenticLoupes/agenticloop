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
  "DEMO-009": { tag: "VERIFY", hint: "A note mentions a medication change; current status unknown", suggested: { procedure: "extraction", tooth: 19 }, thumb: "/assets/imaging/IMG-003.png" },
  "DEMO-010": { tag: "IMAGING", hint: "Radiograph of the extraction site — vision review", suggested: { procedure: "extraction", tooth: 30 }, thumb: "/assets/imaging/IMG-001.png" },
  "DEMO-011": { tag: "IMAGING", hint: "Implant candidate — radiograph of the #8 region on file", suggested: { procedure: "implant", tooth: 8 }, thumb: "/assets/imaging/IMG-004.png" },
  "DEMO-012": { tag: "ALLERGY", hint: "Documented latex sensitivity — relevant to most procedures", suggested: { procedure: "root_canal", tooth: 9 } },
  "DEMO-014": { tag: "ALLERGY", hint: "Documented lidocaine reaction + diabetes", suggested: { procedure: "filling", tooth: 12 } },
  "DEMO-016": { tag: "TRANSCRIPT", hint: "On an anticoagulant; benign visit transcript", suggested: { procedure: "extraction", tooth: 14 } },
  "DEMO-017": { tag: "IMAGING", hint: "Radiograph of the #30 region on file", suggested: { procedure: "crown", tooth: 30 }, thumb: "/assets/imaging/IMG-005.png" },
};

// scenario-type glyph for cases without a film on file (typographic, matches the design)
const TAG_GLYPH: Record<string, string> = {
  "SURFACE + TRANSCRIPT": "Rx",
  SILENCE: "—",
  VERIFY: "?",
  ALLERGY: "!",
  TRANSCRIPT: "“”",
  IMAGING: "▣",
};

export default function PatientSelect({
  onSelect,
}: {
  onSelect: (p: Patient, suggested?: ScenarioSuggestion) => void;
}) {
  const [patients, setPatients] = useState<Patient[] | null>(null);
  const [error, setError] = useState(false);

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
                        className="h-11 w-11 shrink-0 rounded-md border border-stone-200 bg-stone-900 object-cover"
                      />
                    ) : (
                      <span
                        aria-hidden
                        className="flex h-11 w-11 shrink-0 items-center justify-center rounded-md bg-stone-100 font-mono text-sm text-stone-400"
                      >
                        {s ? TAG_GLYPH[s.tag] ?? "·" : "·"}
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
    </section>
  );
}
