"""SHARED CONTRACT -- freeze before anyone writes feature code. plan.md §7.

Mirror of frontend/src/ws.js. If you change one, change both.

TODO -- types only at T+0:30, no logic:
  Box       tooth, x, y, w, h, conf, highlight, label   (coords normalized 0-1)
  Overlay   {"type": "overlay", "boxes": [Box, ...]}
  Flag      {"type": "flag", tooth, severity, message, basis: [str]}
  Transcript / AudioOut / Status
  Client-in: AudioIn {"type":"audio","data":b64}, Frame {"type":"frame","data":b64,"ts":int}
"""
