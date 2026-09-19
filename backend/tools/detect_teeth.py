"""detect_teeth() -> {"boxes": [Box, ...]}   [OWNER: A]

NO frame argument: reads the newest JPEG from server-side session state.

Default implementation: ask gpt-5.6-terra for the visible teeth as normalized
boxes with FDI numbers (a second, cheap vision call with a strict JSON schema).
If the model is unsure of a number it returns tooth="unknown" and the reply
asks the dentist for it -- that is the sanctioned "I don't know" path.

Roboflow `teeth-detection-and-numbering-agi2i/18` is a PANORAMIC X-RAY model
(33 classes, all quadrants in one frame). It will not number teeth in a
cleaning video. Only swap it in if the stretch smoke test proves otherwise.
"""
