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
        className="trace-in max-h-[85vh] w-full max-w-lg overflow-y-auto rounded-t-2xl bg-white p-5 shadow-xl sm:rounded-2xl"
      >
        <div className="mb-4 flex items-start justify-between">
          <div>
            <h3 className="text-xl font-semibold text-stone-900">
              Source record
            </h3>
            <p className="mt-0.5 text-sm text-stone-500">
              Straight from the chart — synthetic demo data.
            </p>
          </div>
          <button
            onClick={onClose}
            aria-label="Close"
            className="-mr-1 flex h-11 w-11 shrink-0 items-center justify-center rounded-lg text-xl text-stone-500 hover:bg-stone-100 hover:text-stone-800"
          >
            ✕
          </button>
        </div>

        {error && (
          <p className="text-[15px] text-stone-700">
            We couldn&apos;t load this record right now. Close and try again.
          </p>
        )}
        {!error && !record && (
          <p className="animate-pulse text-[15px] text-stone-500">
            Loading the record…
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
                    !["id", "patient_id", "recorded_at", "source_label", "image_url", "metadata"].includes(k)
                ),
              ].map(([k, v]) => (
                <div key={String(k)} className="contents">
                  <dt className="text-sm capitalize leading-6 text-stone-500">
                    {String(k).replace(/_/g, " ")}
                  </dt>
                  <dd className="font-mono text-sm leading-6 text-stone-900">
                    {formatValue(v)}
                  </dd>
                </div>
              ))}
            </dl>
            {(() => {
              const meta = record.data.metadata as { description?: string } | null;
              const description = meta && typeof meta === "object" ? meta.description : null;
              return (
                <>
                  {description && (
                    <div className="mt-4 rounded-lg bg-stone-100 px-3.5 py-3">
                      <p className="text-sm font-semibold text-stone-700">
                        Description
                      </p>
                      <p className="mt-1 text-[15px] leading-relaxed text-stone-700">
                        {description}
                      </p>
                    </div>
                  )}
                  {imageUrl && (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={imageUrl}
                      alt={description ?? `Synthetic radiograph ${record.record_id}`}
                      className="mt-4 w-full rounded-lg border border-stone-200"
                    />
                  )}
                </>
              );
            })()}
          </>
        )}
      </div>
    </div>
  );
}
