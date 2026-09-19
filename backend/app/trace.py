"""Agent trace — observable actions only (§20), persisted to agent_event."""
import json
import threading

from app.db import get_conn


class Trace:
    def __init__(self, run_id: str):
        self.run_id = run_id
        self.seq = 0
        self.events: list[dict] = []
        self._lock = threading.Lock()  # LangGraph executes parallel tool calls in threads

    def add(self, agent: str, event_type: str, summary: str, metadata: dict | None = None):
        with self._lock:
            self.seq += 1
            ev = {"sequence_no": self.seq, "agent": agent, "event_type": event_type,
                  "summary": summary, "metadata": metadata or {}}
            self.events.append(ev)
            with get_conn() as c:
                c.execute(
                    "insert into agent_event (run_id, sequence_no, agent, event_type, summary, metadata)"
                    " values (%s,%s,%s,%s,%s,%s)",
                    (self.run_id, self.seq, agent, event_type, summary,
                     json.dumps(ev["metadata"], default=str)),
                )
                c.commit()
