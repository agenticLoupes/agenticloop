"""TypeSafe/Jev wrapper — the Skeptic's typed decisions (user-approved stack override).

Noul -> probability a condition holds; Choice -> one of a defined set.
No confidence percentages are ever shown to the dentist (§9.3/§21).
"""
import os

from typesafe_sdk import Choice, Noul, TypeSafeClient

from app.config import get_settings


def _client() -> TypeSafeClient:
    # SDK reads TYPESAFE_API_KEY from env; ensure it's set from our settings
    os.environ.setdefault("TYPESAFE_API_KEY", get_settings().typesafe_api_key)
    return TypeSafeClient()


def judge(state: dict, nouls: dict[str, str], choice_id: str, choice_instructions: str,
          choice_criteria: list[str]) -> tuple[dict[str, float], str]:
    """Ask the 8-style Noul checks + one Choice over the same state in ONE request.

    Returns ({noul_id: probability}, chosen_option).
    """
    questions: dict = {qid: Noul(instructions=text) for qid, text in nouls.items()}
    questions[choice_id] = Choice(instructions=choice_instructions,
                                  criteria={c: None for c in choice_criteria})
    with _client() as c:
        r = c.system_one(state=state, questions=questions)
    probs = {qid: float(r.nouls[qid].noul) for qid in nouls}
    return probs, str(r.choices[choice_id].choice)
