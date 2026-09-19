"""Wake-phrase gate on the transcript.  [OWNER: A]

Belt and braces: the Live system instruction AND this regex. The instruction
alone leaks. See plan.md §9.

TODO:
  - is_awake(transcript: str) -> bool   # WAKE_PHRASE env, fuzzy-ish match
  - strip the phrase before the turn reaches the model
"""
