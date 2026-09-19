"""Gate 2/5 scenario runner — run A/B/C live and check expected outcomes.

Usage: .venv/bin/python scripts/run_scenarios.py [repeat]
Exit code 0 only if every scenario in every repetition behaves per spec (§8).
"""
import sys

from app.graph import run_investigation

SCENARIOS = [
    # (patient, procedure, tooth, check_fn, description)
    ("DEMO-007", "extraction", 30,
     lambda s: any(c.decision == "SURFACE" and "MED-018" in c.evidence_ids for c in s.final_cards),
     "A: SURFACE active Warfarin (MED-018)"),
    ("DEMO-008", "extraction", 3,
     lambda s: not any(c.decision == "SURFACE" for c in s.final_cards),
     "B: no SURFACE (dismissed or silence)"),
    ("DEMO-009", "extraction", 19,
     lambda s: any(c.decision == "VERIFY" for c in s.final_cards) or s.verify_count > 0,
     "C: VERIFY the medication-change note"),
]


def main(repeat: int = 1) -> int:
    failures = 0
    for i in range(repeat):
        print(f"--- round {i + 1}/{repeat} ---")
        for pid, proc, tooth, check, desc in SCENARIOS:
            s = run_investigation(pid, proc, tooth)
            ok = s.status == "complete" and check(s)
            # evidence contract: every card must carry evidence ids (§12)
            contract = all(c.evidence_ids for c in s.final_cards)
            status = "PASS" if ok and contract else "FAIL"
            if status == "FAIL":
                failures += 1
            print(f"[{status}] {desc} | status={s.status} cards={len(s.final_cards)} "
                  f"dismissed={s.dismissed_count} verify={s.verify_count}"
                  + ("" if contract else " | EVIDENCE CONTRACT VIOLATED"))
    print(f"\n{'ALL PASS' if failures == 0 else f'{failures} FAILURES'}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main(int(sys.argv[1]) if len(sys.argv) > 1 else 1))
