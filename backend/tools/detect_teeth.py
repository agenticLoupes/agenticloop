"""detect_teeth(frame_b64) -> {"boxes": [Box, ...]}   [OWNER: A]

Roboflow `teeth-detection-and-numbering-agi2i/18`. We train nothing.
Smoke-test against a real frame from the demo video at T+0:15 -- if FDI
numbering fails, fall back to generic detection + the dentist speaks the
number. Decide then, not at hour four.
"""
