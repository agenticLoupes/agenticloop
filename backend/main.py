"""FastAPI app + /ws endpoint.  [OWNER: A]

Relays browser <-> Gemini Live. See plan.md §4, §7.1.

TODO:
  - FastAPI app, CORS for the vite dev origin
  - GET /health
  - WS /ws: accept client {audio|frame} frames, fan out
    {transcript|audio|overlay|flag|status} per the §7.1 contract
"""
