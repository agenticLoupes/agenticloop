// The voice layer's tools. Live is only the ears and mouth: every investigation is run
// by the existing Guardian pipeline (POST /investigations), unchanged.

import { Type, type FunctionDeclaration } from "@google/genai";
import {
  getEvidence,
  getRun,
  startInvestigation,
  type InvestigationState,
  type Patient,
} from "@/lib/api";
import type { ToolHandler } from "@/lib/live/session";

export const PROCEDURES = ["extraction", "root_canal", "crown", "filling", "implant", "cleaning"];
const TOOTH_REQUIRED = new Set(["extraction", "root_canal", "crown", "filling", "implant"]);

export const TOOL_DECLARATIONS: FunctionDeclaration[] = [
  {
    name: "start_investigation",
    description:
      "Start Guardian's pre-procedure record review for the current patient. Call as soon as the " +
      "clinician states what they are about to do. Returns immediately; the result arrives later " +
      "as a message starting with [GUARDIAN RESULT].",
    parameters: {
      type: Type.OBJECT,
      properties: {
        procedure: { type: Type.STRING, enum: PROCEDURES, description: "Planned procedure." },
        tooth_number: {
          type: Type.INTEGER,
          description: "Universal tooth number 1-32. Required for every procedure except cleaning.",
        },
      },
      required: ["procedure"],
    },
  },
  {
    name: "get_evidence",
    description:
      "Fetch one source record by its evidence id (e.g. MED-018, ALG-004) so you can answer " +
      "follow-up questions about a result card. Only read out what the record says.",
    parameters: {
      type: Type.OBJECT,
      properties: { evidence_id: { type: Type.STRING } },
      required: ["evidence_id"],
    },
  },
  {
    name: "select_patient",
    description: "Switch to another demo patient when the clinician names one (e.g. 'DEMO-009').",
    parameters: {
      type: Type.OBJECT,
      properties: { patient: { type: Type.STRING, description: "Demo identifier or patient id." } },
      required: ["patient"],
    },
  },
];

export function systemInstruction(patient: Patient | null, patients: Patient[]): string {
  const current = patient ? `${patient.demo_identifier} (${patient.display_name})` : "none selected";
  return `You are Loupes, the voice of DentAssist Guardian: a chairside assistant to the clinician,
working hands-free while their hands are busy. All patient data here is synthetic; this is a prototype.

Your job is the product's promise — before they begin, let the record challenge the plan. You do not
review the record yourself: when the clinician tells you what they are about to do, Guardian (the
record-review agent) investigates that patient's own records and a verifier challenges each finding.

How you work:
- The moment the clinician states a procedure, and a tooth in Universal numbering 1-32, call
  start_investigation. Acknowledge the way an assistant would — "Checking the record for the
  extraction on thirty" — then stay quiet while it runs. It takes 10-60 seconds.
- When a [GUARDIAN RESULT] message arrives, brief them: lead with how many records are worth a look,
  then each one in plain clinical language ("Warfarin is listed as active"), and flag anything the
  verifier could not confirm as needing verification. Offer the source rather than reciting record
  ids: "I can pull the source if you want it." If nothing surfaced, say so plainly — silence is a
  real result, not a failure: "Nothing in the record needs your attention before this one."
- If they ask for detail or the source, call get_evidence and read what the record actually says.
- If they name another patient, call select_patient and confirm the switch.
- You see their camera at about one frame per second. If they point and say "this one", you may read
  the Universal tooth number from the image, but always say it back for confirmation before starting.
  If you cannot read it confidently, just ask — "I can't read that one, which number?"

How you speak:
- Like an assistant briefing a clinician mid-procedure: calm, short, specific. One or two sentences,
  no lists read aloud, no filler, no restating what they just told you.
- The clinician decides. You surface records and never diagnose, interpret findings, recommend
  treatment, or suggest a drug or dose — not even if asked directly. If asked for a clinical opinion,
  say that is their call and offer the records instead.
- Only state patient facts that came from a tool result or a [GUARDIAN RESULT] message. If you do not
  have something, say so. Never guess a record, a date, or a value.
- Stay silent when the room is talking rather than talking to you — patient conversation is not your
  cue. Answer when addressed as "Loupes" or clearly instructed.

Current patient: ${current}.
Demo patients: ${patients.map((p) => p.demo_identifier).join(", ") || "unknown"}.`;
}

/** Spoken-context summary of a finished run, sent to the model as text. */
export function describeResult(r: InvestigationState, patientLabel: string): string {
  const intent =
    r.procedure.replace(/_/g, " ") + (r.tooth_number != null ? ` on tooth #${r.tooth_number}` : "");
  const cards = r.final_cards ?? [];
  const lines = cards.map(
    (c, i) =>
      `${i + 1}. ${c.decision === "SURFACE" ? "worth a look" : "could not be confirmed — needs verification"}: ` +
      `${c.title.replace(/^(Record to review|Item to verify) — /, "")}. ${c.summary} ` +
      `[source: ${c.evidence_ids.join(", ")}]`
  );
  return (
    `[GUARDIAN RESULT] ${patientLabel}, ${intent}. ` +
    (cards.length
      ? `${cards.length} record(s) worth the clinician's attention:\n${lines.join("\n")}`
      : "Nothing in the record needs their attention before this procedure.") +
    (r.dismissed_count ? `\n(${r.dismissed_count} other candidate(s) were challenged and dropped.)` : "") +
    "\nBrief them now, in one or two spoken sentences. Don't read the ids aloud; offer the source instead."
  );
}

export interface ToolContext {
  getPatient: () => Patient | null;
  getPatients: () => Patient[];
  setPatient: (p: Patient) => void;
  onRunStarted: (runId: string, procedure: string, tooth: number | null) => void;
  onRunFinished: (runId: string, result: InvestigationState | null) => void;
  notifyModel: (text: string) => void;
}

const POLL_MS = 1500;
const RUN_TIMEOUT_MS = 180_000;

export function makeHandlers(ctx: ToolContext): Record<string, ToolHandler> {
  return {
    async start_investigation(args) {
      const patient = ctx.getPatient();
      if (!patient) return { error: "No patient selected. Ask the clinician which patient." };
      const procedure = String(args.procedure ?? "").toLowerCase().replace(/\s+/g, "_");
      if (!PROCEDURES.includes(procedure)) {
        return { error: `Unsupported procedure. Supported: ${PROCEDURES.join(", ")}.` };
      }
      const raw = args.tooth_number;
      const tooth = raw == null || raw === "" ? null : Math.round(Number(raw));
      if (TOOTH_REQUIRED.has(procedure) && (tooth == null || !(tooth >= 1 && tooth <= 32))) {
        return { error: "A Universal tooth number 1-32 is required. Ask the clinician for it." };
      }
      const { run_id } = await startInvestigation({
        patient_id: patient.id,
        procedure,
        tooth_number: TOOTH_REQUIRED.has(procedure) ? tooth : null,
      });
      ctx.onRunStarted(run_id, procedure, tooth);
      void followRun(run_id, patient.demo_identifier, ctx);
      return { status: "started", patient: patient.demo_identifier, procedure, tooth_number: tooth };
    },

    async get_evidence(args) {
      const rec = await getEvidence(String(args.evidence_id ?? "").trim().toUpperCase());
      const { image_url: _img, ...data } = rec.data as Record<string, unknown>;
      return { record_id: rec.record_id, type: rec.record_type, recorded_at: rec.recorded_at, data };
    },

    async select_patient(args) {
      const q = String(args.patient ?? "").toUpperCase().replace(/\s+/g, "");
      const digits = q.replace(/\D/g, "");
      const match = ctx.getPatients().find(
        (p) =>
          p.id.toUpperCase() === q ||
          p.demo_identifier.toUpperCase().replace(/\s+/g, "") === q ||
          (!!digits && p.demo_identifier.replace(/\D/g, "").replace(/^0+/, "") === digits.replace(/^0+/, ""))
      );
      if (!match) {
        return { error: "No such patient.", known: ctx.getPatients().map((p) => p.demo_identifier) };
      }
      ctx.setPatient(match);
      return { ok: true, patient: match.demo_identifier };
    },
  };
}

async function followRun(runId: string, patientLabel: string, ctx: ToolContext) {
  const deadline = Date.now() + RUN_TIMEOUT_MS;
  while (Date.now() < deadline) {
    await new Promise((r) => setTimeout(r, POLL_MS));
    try {
      const run = await getRun(runId);
      if (run.status === "complete" && run.result) {
        ctx.onRunFinished(runId, run.result);
        ctx.notifyModel(describeResult(run.result, patientLabel));
        return;
      }
      if (run.status === "error") break;
    } catch {
      /* transient poll failure; keep trying until the deadline */
    }
  }
  ctx.onRunFinished(runId, null);
  ctx.notifyModel(
    "[GUARDIAN RESULT] The investigation could not be completed; no result was invented. " +
      "Tell the clinician briefly and offer to retry."
  );
}
