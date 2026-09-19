"""Gemini Live WSS session manager.  [OWNER: A]

Raw `websockets` on purpose -- LangChain has no bidi-streaming abstraction.
See plan.md §3.1.

Model: gemini-2.5-flash-native-audio-preview-12-2025

TODO:
  - connect / setup message with TOOL_DECLARATIONS + system instruction
  - send PCM16 16kHz audio in, JPEG frames in at 1-2 FPS
  - read PCM16 24kHz audio out + text deltas
  - dispatch function_call -> tools/, send function_response back
  - reconnect on drop
"""
