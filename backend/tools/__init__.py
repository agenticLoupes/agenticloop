"""TOOL_DECLARATIONS for gpt-5.6-terra (Responses API function tools). [OWNER: A]

Three tools, all sync, all returning JSON-serializable dicts (schemas.py).
    detect_teeth()                      -> {"boxes": [Box]}      reads latest frame from session state
    get_tooth_record(tooth, patient_id) -> ToothRecord
    log_finding(tooth, observation, source, confidence) -> {"id": int}   called autonomously

dispatch(name, args, session) is async and runs each sync tool via asyncio.to_thread.
A stubs all three with hardcoded returns first, then wires the real ones.
"""
