"""Rebuild the task-state snapshot by replaying the event log.

The snapshot is derived and disposable; the log is the truth (rule 7).
Fails loudly on any event kind it does not understand: a snapshot built
from a partially-understood log is corrupt by construction.
"""
import json

from . import constants
from .events import read_events


def _apply(tasks: dict, ev: dict, line_no: int) -> None:
    kind = ev["kind"]
    if kind == "create":
        p = ev["payload"]
        tasks[ev["task_id"]] = {
            "task_id": ev["task_id"],
            "code": p["code"],
            "title": p["title"],
            "domain": p["domain"],
            "status": "open",
            "created": ev["ts"],
            "due_date": p.get("due_date"),
            "owner": p.get("owner"),
            "waiting_on": None,
            "blocked": None,
            "snoozed_until": None,
            # Ingest derives these once, at creation, from the full message.
            # Recomputing them later from the title alone loses the sender and
            # the body, which is where the counterparty usually lives.
            "action": p.get("action"),
            "counterparty": p.get("counterparty"),
            "source": p.get("source"),
            "evidence": p.get("evidence"),
            "archived": False,
            "vetoed": False,
            "applied": False,
            "notes": [],
        }
        return
    t = tasks.get(ev["task_id"])
    if t is None:
        raise ValueError(f"event #{line_no}: {kind} for unknown task_id {ev['task_id']!r}")
    p = ev.get("payload", {})
    if kind == "set_status":
        status = p.get("status")
        if status not in constants.STATUSES:
            raise ValueError(f"event #{line_no}: bad status {status!r}")
        t["status"] = status
        if p.get("evidence"):
            t["notes"].append({"ts": ev["ts"], "note": f"evidencia: {p['evidence']}", "actor": ev["actor"]})
    elif kind == "set_due_date":
        t["due_date"] = p.get("due_date")
    elif kind == "set_owner":
        t["owner"] = p.get("owner")
    elif kind == "snooze":
        t["snoozed_until"] = p.get("until")
    elif kind == "set_waiting_on":
        t["waiting_on"] = p.get("who")
    elif kind == "set_blocked":
        t["blocked"] = p.get("reason")
    elif kind == "add_note":
        t["notes"].append({"ts": ev["ts"], "note": p.get("note", ""), "actor": ev["actor"]})
    elif kind == "veto":
        # Permanent and irreversible by design (rule 5): one veto and this is
        # never proposed again. Undoing it takes a new create, not an edit.
        t["vetoed"] = True
        t["archived"] = True
        t["notes"].append({"ts": ev["ts"], "note": f"vetada: {p.get('reason', 'sin razón')}", "actor": ev["actor"]})
    elif kind == "apply_proposal":
        t["applied"] = True
        t["status"] = "done"
        t["notes"].append({"ts": ev["ts"], "note": "propuesta aplicada por Armando", "actor": ev["actor"]})
    elif kind == "archive":
        t["archived"] = True
        t["notes"].append({"ts": ev["ts"], "note": f"archivado: {p.get('reason', 'sin razón')}", "actor": ev["actor"]})
    else:
        # EVENT_KINDS and this dispatcher must stay in lockstep.
        raise ValueError(f"event #{line_no}: kind {kind!r} is whitelisted but has no replay handler — fix replay.py")


def replay(log_path=None) -> dict:
    tasks: dict = {}
    for n, ev in enumerate(read_events(log_path or constants.TASKS_LOG), 1):
        if ev["kind"] not in constants.EVENT_KINDS:
            raise ValueError(f"event #{n}: unknown kind {ev['kind']!r} — refusing to rebuild")
        _apply(tasks, ev, n)
    return tasks


def write_snapshot(tasks: dict, path=None) -> None:
    path = path or constants.SNAPSHOT
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, sort_keys=True, indent=1)
        f.write("\n")
