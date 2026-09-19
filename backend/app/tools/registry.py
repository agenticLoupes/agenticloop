"""LangChain tool bindings, scoped to one patient + traced.

Two consumers, one set of record tools:
- `build_tools`         -> the Guardian's autonomous investigation (§10/§11), vision included.
- `build_advisor_tools` -> the Advisor's dentist-asked question: the same patient-record
                           tools (read-only, same patient scope) PLUS external clinical
                           evidence (PubMed / published guidelines).

Neither agent can ever query another patient: patient_id is closed over here, never a
tool argument the model can set.
"""
from langchain_core.tools import tool

from app.tools import conversations, imaging, literature, records
from app.trace import Trace


def build_tools(patient_id: str, procedure: str, tooth_number, trace: Trace,
                imaging_findings: list | None = None, agent: str = "guardian",
                include_vision: bool = True):
    """imaging_findings: optional list that collects read_imaging results, so the pipeline
    can deterministically promote gate-validated relevant imaging into the candidate pool
    (small models under-report these; the Skeptic still challenges them)."""
    def _dump(rs):
        return [r.model_dump(mode="json") for r in rs]

    @tool
    def get_patient_summary() -> list:
        """Get the patient's summary record."""
        trace.add(agent, "tool_call", "Reviewed patient summary")
        r = records.get_patient_summary(patient_id)
        return _dump([r] if r else [])

    @tool
    def get_dental_history(tooth: int | None = None) -> list:
        """Get dental history events, optionally filtered to one tooth number."""
        trace.add(agent, "tool_call",
                  f"Reviewed tooth #{tooth} history" if tooth else "Reviewed dental history")
        return _dump(records.get_dental_history(patient_id, tooth_number=tooth))

    @tool
    def get_active_medications() -> list:
        """Get the patient's currently active medication records."""
        trace.add(agent, "tool_call", "Reviewed active medication records")
        return _dump(records.get_active_medications(patient_id))

    @tool
    def get_medication_history(medication_name: str | None = None) -> list:
        """Get medication history, optionally for one named medication."""
        trace.add(agent, "tool_call", f"Reviewed medication history"
                  + (f" for {medication_name}" if medication_name else ""))
        return _dump(records.get_medication_history(patient_id, medication_name=medication_name))

    @tool
    def get_allergies() -> list:
        """Get the patient's documented allergy records."""
        trace.add(agent, "tool_call", "Reviewed allergy records")
        return _dump(records.get_allergies(patient_id))

    @tool
    def get_medical_conditions(status: str | None = None) -> list:
        """Get medical condition records, optionally filtered by status ('active' or 'resolved')."""
        trace.add(agent, "tool_call", "Reviewed medical conditions")
        return _dump(records.get_medical_conditions(patient_id, status=status))

    @tool
    def search_clinical_notes(query: str) -> list:
        """Search prior clinical notes for a phrase (e.g. 'medication change')."""
        trace.add(agent, "tool_call", f"Searched clinical notes for '{query}'")
        return _dump(records.search_clinical_notes(patient_id, query))

    @tool
    def search_conversations(query: str) -> list:
        """Search prior visit conversation transcripts for a phrase (e.g. 'blood thinner')."""
        trace.add(agent, "tool_call", f"Searched visit transcripts for '{query}'")
        return _dump(conversations.search_conversations(patient_id, query))

    @tool
    def get_imaging(tooth: int | None = None) -> list:
        """List imaging records (radiographs), optionally for one tooth number."""
        trace.add(agent, "tool_call",
                  f"Reviewed imaging for tooth #{tooth}" if tooth else "Reviewed imaging records")
        return _dump(imaging.get_imaging(patient_id, tooth_number=tooth))

    @tool
    def read_imaging(record_id: str) -> dict:
        """Look at one imaging record to locate its region and check relevance. Never diagnoses."""
        trace.add(agent, "tool_call", f"Inspected imaging record {record_id}")
        result = imaging.read_imaging(record_id, procedure, tooth_number)
        if imaging_findings is not None:
            imaging_findings.append(result)
        return result

    tools = [get_patient_summary, get_dental_history, get_active_medications,
             get_medication_history, get_allergies, get_medical_conditions,
             search_clinical_notes, search_conversations, get_imaging]
    if include_vision:
        tools.append(read_imaging)
    return tools


def build_literature_tools(trace: Trace, agent: str = "advisor"):
    """External clinical evidence. Every result carries a PMID or a URL the dentist can open."""

    @tool
    def search_pubmed(query: str, max_results: int = 4) -> dict:
        """Search PubMed for clinical literature (systematic reviews and trials first).

        Use clinical terminology, e.g. 'dental extraction anticoagulant warfarin bleeding'.
        Returns citations with PMID and URL — cite the PMID for anything you take from here.
        """
        trace.add(agent, "tool_call", f"Searched PubMed for '{query}'")
        out = literature.search_pubmed(query, max_results=max_results)
        if not out.get("available"):
            trace.add(agent, "source_unavailable", f"PubMed unavailable: {out.get('reason')}")
        return out

    @tool
    def search_clinical_guidelines(query: str, site_filter: str = "all") -> dict:
        """Search published dental clinical guidelines for the standard of care.

        site_filter: 'sdcep', 'ada', 'nice', 'cochrane', or 'all'. Returns each page's
        title, URL and snippet — cite the URL for anything you take from here.
        """
        trace.add(agent, "tool_call",
                  f"Searched {site_filter.upper()} clinical guidelines for '{query}'")
        out = literature.search_clinical_guidelines(query, site_filter=site_filter)
        if not out.get("available"):
            trace.add(agent, "source_unavailable",
                      f"Guideline search unavailable: {out.get('reason')}")
        return out

    return [search_pubmed, search_clinical_guidelines]


def build_advisor_tools(patient_id: str | None, procedure: str | None, tooth_number,
                        trace: Trace):
    """The Advisor's toolset: this patient's records (if a patient is in scope) + literature.

    read_imaging is deliberately excluded — the product never interprets a radiograph in
    answer to a question; locating imaging is the Guardian's gated job.
    """
    tools = list(build_literature_tools(trace))
    if patient_id:
        tools = build_tools(patient_id, procedure or "", tooth_number, trace,
                            agent="advisor", include_vision=False) + tools
    return tools
