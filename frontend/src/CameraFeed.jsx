// [OWNER: C]  getUserMedia -> <video>, plus the frame-grab loop.
//
// TODO: grab at 1-2 FPS, canvas -> JPEG -> base64 -> {"type":"frame"}.
// HTTPS is required: getUserMedia is blocked on plain HTTP from a non-localhost
// origin. `vite --host` + ngrok. Get this working at T+0:00 -- it kills more
// demos than any model problem (plan.md §9).
