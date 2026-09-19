// [OWNER: C]  SHARED CONTRACT -- mirror of backend/schemas.py. plan.md §7.1.
// Freeze this before anyone writes feature code. Change one, change both.
//
// Client -> server
//   {"type":"audio", "data":"<b64 PCM16 16kHz mono>"}
//   {"type":"frame", "data":"<b64 JPEG>", "ts":1758300000}
//
// Server -> client
//   {"type":"transcript", "role":"user", "text":"...", "final":true}
//   {"type":"audio", "data":"<b64 PCM16 24kHz>"}
//   {"type":"overlay", "boxes":[{tooth,x,y,w,h,conf,highlight,label}]}
//   {"type":"flag", tooth, severity, message, basis:[...]}   <- pushed unprompted
//   {"type":"status", "state":"idle"}
//
// TODO: connect(), send helpers, and a mock emitter so C can develop offline.
