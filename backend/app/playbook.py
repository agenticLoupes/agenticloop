"""Pattern-informed investigation steering (user-approved "Reading A").

Maps a procedure to record CATEGORIES commonly worth investigating. Steering only:
it influences WHICH of the patient's own records the Guardian inspects. It never
produces advice, and the Guardian remains free to deviate (§10 agency).
"""
# ponytail: static dict, not an ML model
PROCEDURE_PLAYBOOK: dict[str, list[str]] = {
    "extraction": ["get_active_medications", "get_allergies", "get_medical_conditions",
                   "get_dental_history", "search_clinical_notes", "search_conversations",
                   "get_imaging"],
    "root_canal": ["get_dental_history", "get_allergies", "get_active_medications", "get_imaging"],
    "implant": ["get_medical_conditions", "get_active_medications", "get_imaging", "get_dental_history"],
    "crown": ["get_dental_history", "get_allergies"],
    "filling": ["get_dental_history", "get_allergies"],
    "cleaning": ["get_allergies", "get_medical_conditions"],
}


def hint_tools_for(procedure: str) -> list[str]:
    return PROCEDURE_PLAYBOOK.get(procedure.lower().strip().replace(" ", "_"), [])
