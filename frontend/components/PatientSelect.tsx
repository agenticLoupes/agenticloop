"use client";

import { useEffect, useState } from "react";
import { getPatients, type Patient } from "@/lib/api";

export default function PatientSelect({
  onSelect,
}: {
  onSelect: (p: Patient) => void;
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
          {patients.map((p) => (
            <li key={p.id}>
              <button
                onClick={() => onSelect(p)}
                className="flex w-full items-center justify-between px-4 py-3 text-left transition-colors hover:bg-teal-50/60 focus-visible:bg-teal-50/60 focus-visible:outline-none"
              >
                <span>
                  <span className="block font-mono text-sm font-medium text-stone-800">
                    {p.demo_identifier}
                  </span>
                  <span className="block text-xs text-stone-500">
                    {p.display_name}
                  </span>
                </span>
                <span aria-hidden className="text-teal-700">
                  →
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
