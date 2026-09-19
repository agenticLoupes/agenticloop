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
  "DEMO-007": { tag: "Medication", hint: "Active Warfarin — and a visit transcript that contradicts it", suggested: { procedure: "extraction", tooth: 30 } },
  "DEMO-008": { tag: "Nothing to flag", hint: "Stale history only — the agent should stay quiet", suggested: { procedure: "extraction", tooth: 3 } },
  "DEMO-009": { tag: "Needs checking", hint: "A note mentions a medication change; current status unknown", suggested: { procedure: "extraction", tooth: 19 }, thumb: "/assets/imaging/IMG-003_thumb.png" },
  "DEMO-010": { tag: "Radiograph", hint: "Radiograph of the extraction site — vision review", suggested: { procedure: "extraction", tooth: 30 }, thumb: "/assets/imaging/IMG-001_thumb.png" },
  "DEMO-011": { tag: "Radiograph", hint: "Implant candidate — radiograph of the #8 region on file", suggested: { procedure: "implant", tooth: 8 }, thumb: "/assets/imaging/IMG-004_thumb.png" },
  "DEMO-012": { tag: "Allergy", hint: "Documented latex sensitivity — relevant to most procedures", suggested: { procedure: "root_canal", tooth: 9 } },
  "DEMO-014": { tag: "Allergy", hint: "Documented lidocaine reaction + diabetes", suggested: { procedure: "filling", tooth: 12 } },
  "DEMO-016": { tag: "Visit transcript", hint: "On an anticoagulant; benign visit transcript", suggested: { procedure: "extraction", tooth: 14 } },
  "DEMO-017": { tag: "Radiograph", hint: "Radiograph of the #30 region on file", suggested: { procedure: "crown", tooth: 30 }, thumb: "/assets/imaging/IMG-005_thumb.png" },
};

const PROCEDURE_LABELS: Record<string, string> = {
  extraction: "Extraction",
  root_canal: "Root canal",
  crown: "Crown",
  filling: "Filling",
  implant: "Implant",
  cleaning: "Cleaning",
};

// Category tile colors — the avatar should read at a glance, not as an empty square.
const TAG_STYLE: Record<string, string> = {
  "Medication": "border-amber-200 bg-amber-100 text-amber-800",
  "Allergy": "border-rose-200 bg-rose-100 text-rose-700",
  "Visit transcript": "border-sky-200 bg-sky-100 text-sky-800",
  "Needs checking": "border-violet-200 bg-violet-100 text-violet-800",
  "Nothing to flag": "border-stone-300 bg-stone-200 text-stone-700",
  "Radiograph": "border-teal-200 bg-teal-100 text-teal-800",
};
const TAG_BADGE: Record<string, string> = {
  "Medication": "bg-amber-100 text-amber-900",
  "Allergy": "bg-rose-100 text-rose-800",
  "Visit transcript": "bg-sky-100 text-sky-900",
  "Needs checking": "bg-violet-100 text-violet-900",
  "Nothing to flag": "bg-stone-200 text-stone-700",
  "Radiograph": "bg-teal-100 text-teal-900",
};

// scenario-type icon for cases without a film on file (stroke SVGs, clinical style)
function TagIcon({ tag }: { tag: string }) {
  const cls = "h-7 w-7";
  switch (tag) {
    case "Medication": // two-tone capsule
      return (
        <svg viewBox="0 0 24 24" className={cls} aria-hidden>
          <g transform="rotate(-40 12 12)">
            <rect x="3" y="8.5" width="18" height="7.5" rx="3.75" fill="currentColor" />
            <path d="M12 8.5 H17.25 A3.75 3.75 0 0 1 21 12.25 V12.25 A3.75 3.75 0 0 1 17.25 16 H12 Z" fill="#fff" fillOpacity="0.55" />
            <line x1="12" y1="8.5" x2="12" y2="16" stroke="currentColor" strokeWidth="1.4" />
          </g>
        </svg>
      );
    case "Allergy": // filled warning triangle
      return (
        <svg viewBox="0 0 24 24" className={cls} aria-hidden>
          <path d="M12.9 3.6 22 19.4a1 1 0 0 1-.9 1.5H2.9a1 1 0 0 1-.9-1.5L11.1 3.6a1 1 0 0 1 1.8 0Z" fill="currentColor" />
          <rect x="11" y="8.4" width="2" height="6" rx="1" fill="#fff" />
          <circle cx="12" cy="17.2" r="1.15" fill="#fff" />
        </svg>
      );
    case "Visit transcript": // filled speech bubble
      return (
        <svg viewBox="0 0 24 24" className={cls} aria-hidden>
          <path d="M4 4.5h16a1.5 1.5 0 0 1 1.5 1.5v9a1.5 1.5 0 0 1-1.5 1.5h-8.2L7 21v-4.5H4A1.5 1.5 0 0 1 2.5 15V6A1.5 1.5 0 0 1 4 4.5Z" fill="currentColor" />
          <rect x="6" y="8" width="12" height="1.8" rx="0.9" fill="#fff" />
          <rect x="6" y="11.6" width="8" height="1.8" rx="0.9" fill="#fff" />
        </svg>
      );
    case "Needs checking": // magnifier with question mark
      return (
        <svg viewBox="0 0 24 24" className={cls} aria-hidden>
          <circle cx="10.5" cy="10.5" r="7.2" fill="currentColor" />
          <rect x="15.2" y="15.8" width="7" height="3" rx="1.5" transform="rotate(45 15.2 15.8)" fill="currentColor" />
          <path d="M8.7 8.6a2 2 0 1 1 2.9 2c-0.6 0.35-0.85 0.7-0.85 1.4" fill="none" stroke="#fff" strokeWidth="1.7" strokeLinecap="round" />
          <circle cx="10.6" cy="14.1" r="0.95" fill="#fff" />
        </svg>
      );
    case "Nothing to flag": // muted bell with slash
      return (
        <svg viewBox="0 0 24 24" className={cls} aria-hidden>
          <path d="M7 16.4v-5a5 5 0 0 1 10 0v5l1.4 1.8a0.6 0.6 0 0 1-0.5 1H6.1a0.6 0.6 0 0 1-0.5-1L7 16.4Z" fill="currentColor" />
          <path d="M10.1 20.3a2 2 0 0 0 3.8 0" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" />
          <line x1="3.6" y1="3.6" x2="20.4" y2="20.4" stroke="#fff" strokeWidth="3.4" strokeLinecap="round" />
          <line x1="3.6" y1="3.6" x2="20.4" y2="20.4" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" />
        </svg>
      );
    case "Radiograph": // dark film with tooth silhouettes
      return (
        <svg viewBox="0 0 24 24" className={cls} aria-hidden>
          <rect x="2.5" y="4.5" width="19" height="15" rx="2.2" fill="currentColor" />
          <path d="M7.4 11.6v-1.5a1.7 1.7 0 0 1 3.4 0v1.5l-0.7 4a0.5 0.5 0 0 1-1 0l-0.3-2-0.3 2a0.5 0.5 0 0 1-1 0Z" fill="#fff" fillOpacity="0.85" />
          <path d="M13.2 11.6v-1.5a1.7 1.7 0 0 1 3.4 0v1.5l-0.7 4a0.5 0.5 0 0 1-1 0l-0.3-2-0.3 2a0.5 0.5 0 0 1-1 0Z" fill="#fff" fillOpacity="0.85" />
        </svg>
      );
    default:
      return (
        <svg viewBox="0 0 24 24" className={cls} aria-hidden>
          <circle cx="12" cy="12" r="5" fill="currentColor" />
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
      <p className="mb-6 rounded-xl border border-teal-200 bg-teal-50 px-4 py-3.5 text-sm leading-relaxed text-teal-950">
        Guardian reads the patient&apos;s record <em>before</em> the procedure —
        medications, allergies, notes and imaging — questions what it finds, and
        shows you only what is backed by a real record.
      </p>
      <h2 className="mb-1 text-lg font-semibold text-stone-900">
        Choose a patient
      </h2>
      <p className="mb-4 text-sm text-stone-600">
        Each demo patient shows a different kind of finding.
      </p>
      {error && (
        <div className="rounded-xl border border-stone-200 bg-white p-4 shadow-sm">
          <p className="text-sm text-stone-700">
            We couldn&apos;t load the patient list. The demo server may still be
            starting up.
          </p>
          <button
            onClick={load}
            className="mt-3 min-h-11 rounded-lg bg-teal-800 px-5 text-sm font-semibold text-white hover:bg-teal-700"
          >
            Try again
          </button>
        </div>
      )}
      {!error && !patients && (
        <ul
          className="divide-y divide-stone-200 overflow-hidden rounded-xl border border-stone-200 bg-white"
          aria-label="Loading patients"
        >
          {[0, 1, 2, 3].map((i) => (
            <li key={i} className="flex animate-pulse items-center gap-3 px-4 py-4">
              <span className="h-12 w-12 shrink-0 rounded-lg bg-stone-100" />
              <span className="flex-1 space-y-2">
                <span className="block h-3.5 w-28 rounded bg-stone-100" />
                <span className="block h-3 w-44 rounded bg-stone-100" />
              </span>
            </li>
          ))}
        </ul>
      )}
      {patients && (
        <ul className="divide-y divide-stone-200 overflow-hidden rounded-xl border border-stone-200 bg-white shadow-sm">
          {[...patients]
            .filter((p) => showAll || SCENARIO_HINTS[p.id])
            .sort((a, b) => (SCENARIO_HINTS[b.id] ? 1 : 0) - (SCENARIO_HINTS[a.id] ? 1 : 0))
            .map((p) => {
              const s = SCENARIO_HINTS[p.id];
              return (
                <li key={p.id}>
                  <button
                    onClick={() => onSelect(p, s?.suggested)}
                    className="flex w-full items-center gap-3.5 px-4 py-4 text-left transition-colors hover:bg-teal-50 focus-visible:bg-teal-50 focus-visible:outline-none"
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
                        className={
                          "flex h-12 w-12 shrink-0 items-center justify-center rounded-lg border " +
                          (TAG_STYLE[s?.tag ?? ""] ??
                            "border-stone-200 bg-stone-100 text-stone-600")
                        }
                      >
                        <TagIcon tag={s?.tag ?? ""} />
                      </span>
                    )}
                    <span className="min-w-0 flex-1">
                      <span className="flex flex-wrap items-center gap-2">
                        <span className="font-mono text-[15px] font-semibold text-stone-900">
                          {p.demo_identifier}
                        </span>
                        {s && (
                          <span
                            className={
                              "rounded-full px-2.5 py-0.5 text-xs font-medium " +
                              (TAG_BADGE[s.tag] ?? "bg-stone-100 text-stone-700")
                            }
                          >
                            {s.tag}
                          </span>
                        )}
                      </span>
                      <span className="mt-1 block text-sm leading-snug text-stone-600">
                        {s ? s.hint : p.display_name}
                      </span>
                      {s && (
                        <span className="mt-1.5 block text-sm text-stone-500">
                          Suggested: {PROCEDURE_LABELS[s.suggested.procedure] ?? s.suggested.procedure}
                          {s.suggested.tooth != null && `, tooth #${s.suggested.tooth}`}
                        </span>
                      )}
                    </span>
                    <span aria-hidden className="shrink-0 text-lg text-teal-700">
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
          className="mt-3 min-h-11 w-full rounded-lg text-center text-sm font-medium text-stone-600 underline underline-offset-2 hover:text-teal-800"
        >
          {showAll
            ? "Hide other patients"
            : `Show ${patients.filter((p) => !SCENARIO_HINTS[p.id]).length} other patients`}
        </button>
      )}
    </section>
  );
}
