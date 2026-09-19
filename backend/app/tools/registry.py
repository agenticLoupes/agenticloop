"""LangChain tool bindings for the Guardian, scoped to one patient + traced.

The Guardian chooses among these (§10/§11); it can never query another patient.
"""
from langchain_core.tools import tool

from app.tools import records, imaging, conversations
from app.trace import Trace


def build_tools(patient_id: str, procedure: str, tooth_number, trace: Trace,
                imaging_findings: list | None = None):
    """imaging_findings: optional list that collects read_imaging results, so the pipeline
    can deterministically promote gate-validated relevant imaging into the candidate pool
    (small models under-report these; the Skeptic still challenges them)."""
    def _dump(rs):
        return [r.model_dump(mode="json") for r in rs]

    @tool
    def get_patient_summary() -> list:
        """Get the patient's summary record."""
        trace.add("guardian", "tool_call", "Reviewed patient summary")
        r = records.get_patient_summary(patient_id)
        return _dump([r] if r else [])

    @tool
    def get_dental_history(tooth: int | None = None) -> list:
        """Get dental history events, optionally filtered to one tooth number."""
        trace.add("guardian", "tool_call",
                  f"Reviewed tooth #{tooth} history" if tooth else "Reviewed dental history")
        return _dump(records.get_dental_history(patient_id, tooth_number=tooth))

    @tool
    def get_active_medications() -> list:
        """Get the patient's currently active medication records."""
        trace.add("guardian", "tool_call", "Reviewed active medication records")
        return _dump(records.get_active_medications(patient_id))

    @tool
    def get_medication_history(medication_name: str | None = None) -> list:
        """Get medication history, optionally for one named medication."""
        trace.add("guardian", "tool_call", f"Reviewed medication history"
                  + (f" for {medication_name}" if medication_name else ""))
        return _dump(records.get_medication_history(patient_id, medication_name=medication_name))

    @tool
    def get_allergies() -> list:
        """Get the patient's documented allergy records."""
        trace.add("guardian", "tool_call", "Reviewed allergy records")
        return _dump(records.get_allergies(patient_id))

    @tool
    def get_medical_conditions(status: str | None = None) -> list:
        """Get medical condition records, optionally filtered by status ('active' or 'resolved')."""
        trace.add("guardian", "tool_call", "Reviewed medical conditions")
        return _dump(records.get_medical_conditions(patient_id, status=status))

    @tool
    def search_clinical_notes(query: str) -> list:
        """Search prior clinical notes for a phrase (e.g. 'medication change')."""
        trace.add("guardian", "tool_call", f"Searched clinical notes for '{query}'")
        return _dump(records.search_clinical_notes(patient_id, query))

    @tool
    def search_conversations(query: str) -> list:
        """Search prior visit conversation transcripts for a phrase (e.g. 'blood thinner')."""
        trace.add("guardian", "tool_call", f"Searched visit transcripts for '{query}'")
        return _dump(conversations.search_conversations(patient_id, query))

    @tool
    def get_imaging(tooth: int | None = None) -> list:
        """List imaging records (radiographs), optionally for one tooth number."""
        trace.add("guardian", "tool_call",
                  f"Reviewed imaging for tooth #{tooth}" if tooth else "Reviewed imaging records")
        return _dump(imaging.get_imaging(patient_id, tooth_number=tooth))

    @tool
    def read_imaging(record_id: str) -> dict:
        """Look at one imaging record to locate its region and check relevance. Never diagnoses."""
        trace.add("guardian", "tool_call", f"Inspected imaging record {record_id}")
        result = imaging.read_imaging(record_id, procedure, tooth_number)
        if imaging_findings is not None:
            imaging_findings.append(result)
        return result

    return [get_patient_summary, get_dental_history, get_active_medications,
            get_medication_history, get_allergies, get_medical_conditions,
            search_clinical_notes, search_conversations, get_imaging, read_imaging]
