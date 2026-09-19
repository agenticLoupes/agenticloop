// [OWNER: C]  Mic capture and playback.
//
// In:  mic -> PCM16 16kHz mono -> base64 -> {"type":"audio"}
// Out: {"type":"audio"} PCM16 24kHz -> AudioContext queue, gapless.
//
// Sample-rate mismatch is the classic 2-hour sink. Budgeted in the 3:00-4:30
// block (plan.md §13).
