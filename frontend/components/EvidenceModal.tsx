"use client";

import { useEffect, useState } from "react";
import { API_URL, getEvidence, type EvidenceRecord } from "@/lib/api";

function formatValue(v: unknown): string {
  if (v === null || v === undefined || v === "") return "—";
  if (typeof v === "object")
    return Object.keys(v as object).length ? JSON.stringify(v) : "—";
  return String(v);
}

export default function EvidenceModal({
  evidenceId,
  onClose,
}: {
  evidenceId: string;
  onClose: () => void;
}) {
  const [record, setRecord] = useState<EvidenceRecord | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    setRecord(null);
    setError(false);
    getEvidence(evidenceId).then(setRecord, () => setError(true));
  }, [evidenceId]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const imageUrl =
    record?.record_type === "imaging" &&
    typeof record.data.image_url === "string"
      ? API_URL + record.data.image_url
      : null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-stone-900/50 sm:items-center"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label={`Source record ${evidenceId}`}
        onClick={(e) => e.stopPropagation()}
        className="trace-in max-h-[85vh] w-full max-w-md overflow-y-auto rounded-t-xl bg-white p-5 shadow-xl sm:rounded-xl"
      >
        <div className="mb-4 flex items-start justify-between">
          <div>
            <h3 className="font-[family-name:var(--font-display)] text-lg font-semibold uppercase tracking-tight text-stone-900">
              Source record
            </h3>
            <p className="text-[10px] font-medium uppercase tracking-[0.2em] text-stone-400">
              Synthetic record
            </p>
          </div>
          <button
            onClick={onClose}
            aria-label="Close"
            className="rounded-md px-2 py-1 text-stone-400 hover:bg-stone-100 hover:text-stone-700"
          >
            ✕
          </button>
        </div>

        {error && (
          <p className="text-sm text-stone-600">
            Recoverable demo error — source record unavailable.
          </p>
        )}
        {!error && !record && (
          <p className="animate-pulse font-mono text-sm text-stone-400">
            Loading record…
          </p>
        )}
        {record && (
          <>
            <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1.5 text-sm">
              {[
                ["Record", record.record_id],
                ["Type", record.record_type.replace(/_/g, " ")],
                ["Patient", record.patient_id],
                ["Source", record.source_label],
                [
                  "Recorded",
                  new Date(record.recorded_at).toLocaleDateString("en-US", {
                    year: "numeric",
                    month: "short",
                    day: "numeric",
                  }),
                ],
                ...Object.entries(record.data).filter(
                  ([k]) =>
                    !["id", "patient_id", "recorded_at", "source_label", "image_url"].includes(k)
                ),
              ].map(([k, v]) => (
                <div key={String(k)} className="contents">
                  <dt className="text-[10px] font-medium uppercase leading-6 tracking-[0.15em] text-stone-400">
                    {String(k).replace(/_/g, " ")}
                  </dt>
                  <dd className="font-mono text-[13px] leading-6 text-stone-800">
                    {formatValue(v)}
                  </dd>
                </div>
              ))}
            </dl>
            {imageUrl && (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={imageUrl}
                alt={`Synthetic radiograph ${record.record_id}`}
                className="mt-4 w-full rounded-md border border-stone-200"
              />
            )}
          </>
        )}
      </div>
    </div>
  );
}
