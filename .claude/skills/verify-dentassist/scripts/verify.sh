#!/usr/bin/env bash
# verify-dentassist helper: launch | doctor | drive [patient] [procedure] [tooth] | cleanup
set -u
ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
V="$ROOT/.verify"; mkdir -p "$V"
BE="$ROOT/backend"; FE="$ROOT/frontend"
PY="$BE/.venv/bin/python"; UVICORN="$BE/.venv/bin/uvicorn"
NPM="${NPM:-/opt/homebrew/bin/npm}"; command -v "$NPM" >/dev/null || NPM=npm
API=http://localhost:8000; UI=http://localhost:3000

ok(){ printf '  \033[32mPASS\033[0m %s\n' "$*"; }
bad(){ printf '  \033[31mFAIL\033[0m %s\n' "$*"; FAILS=$((FAILS+1)); }
FAILS=0

alive(){ [ -f "$1" ] && kill -0 "$(cat "$1")" 2>/dev/null; }

launch(){
  [ -f "$BE/.env" ] || { [ -f "$ROOT/.env" ] && command cp "$ROOT/.env" "$BE/.env" && echo "copied root .env -> backend/.env"; }
  [ -x "$UVICORN" ] || { echo "backend venv missing: see SKILL.md prerequisites"; exit 1; }
  if alive "$V/backend.pid"; then echo "backend already running (pid $(cat "$V/backend.pid"))"; else
    # exec so the pid we record IS uvicorn, and all three std fds leave the caller's pipe
    ( cd "$BE" && exec env -u GOOGLE_API_KEY -u GEMINI_API_KEY -u GOOGLE_GENERATIVE_AI_API_KEY \
        "$UVICORN" app.main:app --port 8000 ) >| "$V/backend.log" 2>&1 </dev/null &
    echo $! >| "$V/backend.pid"
  fi
  [ -d "$FE/.next" ] || ( cd "$FE" && "$NPM" run build >| "$V/frontend-build.log" 2>&1 ) || { echo "frontend build failed, see $V/frontend-build.log"; exit 1; }
  if alive "$V/frontend.pid"; then echo "frontend already running (pid $(cat "$V/frontend.pid"))"; else
    ( cd "$FE" && PORT=3000 exec "$NPM" run start ) >| "$V/frontend.log" 2>&1 </dev/null &
    echo $! >| "$V/frontend.pid"
  fi
  for i in $(seq 1 40); do curl -sf "$API/health" >/dev/null 2>&1 && break; sleep 1; done
  for i in $(seq 1 40); do curl -sf "$UI/" >/dev/null 2>&1 && break; sleep 1; done
  curl -sf "$API/health" >/dev/null && ok "backend ready on 8000" || bad "backend not answering (see $V/backend.log)"
  curl -sf "$UI/" | grep -q "DentAssist Guardian" && ok "frontend ready on 3000" || bad "frontend not answering (see $V/frontend.log)"
  exit $FAILS
}

doctor(){
  alive "$V/backend.pid" && ok "backend pid $(cat "$V/backend.pid") alive" || bad "no live backend pid in $V"
  alive "$V/frontend.pid" && ok "frontend pid $(cat "$V/frontend.pid") alive" || bad "no live frontend pid in $V"
  # the pid files hold the nohup wrappers; the listener is a child, so walk up the parent chain
  ours(){ local p=$1 mine=" $(cat "$V/backend.pid" "$V/frontend.pid" 2>/dev/null | tr '\n' ' ') "; for _ in 1 2 3 4; do [ -z "$p" ] || [ "$p" = 1 ] && return 1; echo "$mine" | grep -q " $p " && return 0; p=$(ps -o ppid= -p "$p" 2>/dev/null | tr -d ' '); done; return 1; }
  for p in 8000 3000; do owner=$(lsof -ti tcp:$p -sTCP:LISTEN 2>/dev/null | head -1)
    if [ -z "$owner" ]; then bad "nothing listening on $p"; elif ours "$owner"; then ok "port $p owned by our process tree (pid $owner)"; else bad "port $p owned by foreign pid $owner: do not drive, do not kill"; fi; done
  h=$(curl -s "$API/health"); echo "$h" | grep -q '"ok":true' && ok "health: $h" || bad "health: $h"
  n=$(curl -s "$API/demo/patients" | "$PY" -c 'import sys,json; print(len(json.load(sys.stdin)))' 2>/dev/null); [ "${n:-0}" -ge 1 ] && ok "database answers: $n demo patients" || bad "demo/patients returned nothing (Supabase down or DB URL wrong)"
  k=$(grep -E '^GOOGLE_API_KEY=' "$BE/.env" | cut -d= -f2- | tr -d '"'"'"' ' ); m=$(grep -E '^GEMINI_MODEL=' "$BE/.env" | cut -d= -f2- | tr -d ' ')
  code=$(curl -s -o "$V/models.json" -w '%{http_code}' "https://generativelanguage.googleapis.com/v1beta/models?key=$k")
  [ "$code" = 200 ] && ok "Gemini key valid (models endpoint 200)" || bad "Gemini key rejected (HTTP $code)"
  "$PY" -c "import json,sys; ms=[x['name'].split('/')[-1] for x in json.load(open('$V/models.json')).get('models',[])]; sys.exit(0 if '$m' in ms else 1)" 2>/dev/null && ok "GEMINI_MODEL=$m is available" || bad "GEMINI_MODEL=$m not in the key's model list"
  env | grep -qE '^(GOOGLE_API_KEY|GEMINI_API_KEY)=' && echo "  note: your shell exports GOOGLE_API_KEY/GEMINI_API_KEY; the helper unsets them for the backend"
  exit $FAILS
}

drive(){
  pid=${1:-DEMO-007}; proc=${2:-extraction}; tooth=${3:-30}
  ts=$(date +%Y%m%d-%H%M%S); E="$V/evidence/$ts"; mkdir -p "$E"
  curl -s "$API/health" >| "$E/health.json"; curl -s "$API/demo/patients" >| "$E/patients.json"
  resp=$(curl -s -XPOST "$API/investigations" -H content-type:application/json -d "{\"patient_id\":\"$pid\",\"procedure\":\"$proc\",\"tooth_number\":$tooth}")
  run=$(echo "$resp" | "$PY" -c 'import sys,json; print(json.load(sys.stdin).get("run_id",""))' 2>/dev/null)
  [ -n "$run" ] && ok "POST /investigations -> run $run" || { bad "POST /investigations failed: $resp"; echo "$resp" >| "$E/summary.txt"; exit 1; }
  t0=$(date +%s); st=running
  while [ $(( $(date +%s) - t0 )) -lt 180 ]; do
    st=$(curl -s "$API/investigations/$run" | "$PY" -c 'import sys,json; print(json.load(sys.stdin).get("status",""))' 2>/dev/null)
    case "$st" in complete|error) break;; esac; sleep 2
  done
  curl -s "$API/investigations/$run" >| "$E/investigation.json"; curl -s "$API/investigations/$run/trace" >| "$E/trace.json"
  el=$(( $(date +%s) - t0 ))
  [ "$st" = complete ] && ok "status complete in ${el}s" || bad "status=$st after ${el}s: $("$PY" -c "import json; print((json.load(open('$E/investigation.json')).get('result') or {}).get('error'))")"
  "$PY" - "$E" <<'PY'
import json,sys,os
E=sys.argv[1]; d=json.load(open(f"{E}/investigation.json")); r=d.get("result") or {}
t=json.load(open(f"{E}/trace.json")); steps=t if isinstance(t,list) else t.get("steps",t.get("trace",[]))
kinds={(s.get("agent"),s.get("event_type")) for s in steps}
checks=[("guardian tool_call in trace",("guardian","tool_call") in kinds),
        ("skeptic decision in trace",("skeptic","decision") in kinds),
        ("composer cards in trace",("composer","cards") in kinds),
        ("run row readable by id (side effect)", d.get("id") is not None and d.get("status") is not None)]
cards=r.get("final_cards",[])
lines=[]
for name,okk in checks:
    print(("  \033[32mPASS\033[0m " if okk else "  \033[31mFAIL\033[0m ")+name); lines.append(("PASS " if okk else "FAIL ")+name)
print(f"  cards={len(cards)} candidates={len(r.get('candidate_evidence',[]))} skeptic={len(r.get('skeptic_results',[]))} verify={r.get('verify_count')} dismissed={r.get('dismissed_count')} trace_steps={len(steps)}")
for c in cards: print("   -", c.get("decision"), "|", c.get("title"))
lines.append(f"status={d.get('status')} cards={len(cards)} steps={len(steps)} run={d.get('id')}")
open(f"{E}/summary.txt","w").write("\n".join(lines)+"\n")
sys.exit(0 if all(o for _,o in checks) else 1)
PY
  rc=$?; echo "  evidence: $E"; exit $(( rc + FAILS ))
}

# kill a pid and every descendant (npm -> next-server is two levels deep); never by name
killtree(){ local p=$1; for c in $(pgrep -P "$p" 2>/dev/null); do killtree "$c"; done; kill "$p" 2>/dev/null; sleep 0.3; kill -9 "$p" 2>/dev/null; }

cleanup(){
  for n in backend frontend; do
    if [ -f "$V/$n.pid" ]; then p=$(cat "$V/$n.pid"); if kill -0 "$p" 2>/dev/null; then killtree "$p"; echo "stopped $n (pid $p and its children)"; else echo "$n pid $p already gone"; fi; command rm -f "$V/$n.pid"; else echo "no $n.pid"; fi
  done
  ls -d "$V"/evidence/* 2>/dev/null | sed 's/^/kept evidence: /'
}

case "${1:-}" in launch) launch;; doctor) doctor;; drive) shift; drive "$@";; cleanup) cleanup;; *) echo "usage: $0 launch|doctor|drive [patient] [procedure] [tooth]|cleanup"; exit 2;; esac
