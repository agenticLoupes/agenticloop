# Pick a patient

First screen. Lists the twelve synthetic patients from `GET /demo/patients`; demo scenario patients sort first and carry a badge plus a hint of the scenario they exercise. Selecting one moves to the procedure step and may pre-fill procedure and tooth from the scenario suggestion.

## Sub-features
- Patient list with `display_name` and `demo_identifier` (DEMO-007 … DEMO-018)
- Scenario badge and hint on demo cases
- Reload button if the list fails to load
- Pre-fill of procedure and tooth from the scenario suggestion

## How to get to it (user POV)
Open `http://localhost:3000`. The list is the landing state (`step === "patient"` in `frontend/app/page.tsx`).

## Driving it with agent-browser / curl
- API: `curl -s localhost:8000/demo/patients` returns 12 rows with `id`, `demo_identifier`, `display_name`.
- UI: `agent-browser snapshot -i` shows one button per patient whose name contains the display name, e.g. "Synthetic Patient 007". Click it and re-snapshot: the procedure form appears.

## Gotchas
- An empty list with a reload button means the backend cannot reach Supabase; run `verify.sh doctor`.
- Patients are backend-served; `NEXT_PUBLIC_API_URL` defaults to `http://localhost:8000` (`frontend/lib/api.ts`).
