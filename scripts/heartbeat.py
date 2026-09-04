#!/usr/bin/env python3
"""Write one heartbeat line. Proof that a routine started, before it can hang.

This exists as a file rather than an inline one-liner in the routine prompt for
two reasons: rule 8 (thin prompts, fat scripts), and because the one-liner had
to be chained after a `cd`, and `cd <dir> && git ...` trips the harness check
for git hooks running from an untrusted directory — which prompted Armando on
every single run.

  heartbeat.py start|end <task-name>
"""
import json
import pathlib
import sys
from datetime import datetime, timezone

REPO = pathlib.Path(__file__).resolve().parents[1]


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in ("start", "end"):
        raise SystemExit("uso: heartbeat.py start|end <task-name>")
    stage, task = sys.argv[1], sys.argv[2]
    now = datetime.now(timezone.utc)
    path = REPO / "syncs" / f"{now.date()}.ndjson"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": now.isoformat(timespec="seconds"), "leg": "heartbeat",
                            "stage": stage, "task": task}, sort_keys=True) + "\n")
    print(f"{stage} {task}")


if __name__ == "__main__":
    main()
