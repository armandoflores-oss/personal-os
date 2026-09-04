#!/usr/bin/env python3
"""Task CLI: the only sanctioned way to touch tasks.ndjson.

  task.py create --title "..." --domain <slug> [--due YYYY-MM-DD] [--actor user]
  task.py event --code T-3 --kind set_status --payload '{"status": "done", "evidence": "..."}'
  task.py rebuild            # replay log -> snapshot -> rendered view
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import constants
from lib.codes import next_code, resolve_code
from lib.events import append_event
from lib.replay import replay, write_snapshot


def render(tasks: dict) -> None:
    """Write the human-readable task view. Firewalled domains render count-only."""
    lines = ["# Tareas abiertas", "", "<!-- Vista generada — NO editar a mano. Regenerar: python3 scripts/task.py rebuild -->", ""]
    for slug, display in constants.DOMAINS:
        rows = [t for t in tasks.values()
                if t["domain"] == slug and not t["archived"] and t["status"] == "open"]
        if not rows:
            continue
        if slug in constants.FIREWALLED_DOMAINS:
            lines.append(f"## {display}")
            lines.append(f"- {len(rows)} pendiente(s) — dominio sellado, detalle solo en el log")
            lines.append("")
            continue
        lines.append(f"## {display}")
        for t in sorted(rows, key=lambda t: (t["due_date"] or "9999", t["code"])):
            due = f" · vence {t['due_date']}" if t["due_date"] else ""
            wait = f" · esperando a {t['waiting_on']}" if t["waiting_on"] else ""
            lines.append(f"- **{t['code']}** {t['title']}{due}{wait}")
        lines.append("")
    constants.TASKS_VIEW.parent.mkdir(parents=True, exist_ok=True)
    constants.TASKS_VIEW.write_text("\n".join(lines) + "\n", encoding="utf-8")


def cmd_rebuild(_args) -> None:
    tasks = replay()
    write_snapshot(tasks)
    render(tasks)
    open_n = sum(1 for t in tasks.values() if t["status"] == "open" and not t["archived"])
    print(f"snapshot rebuilt: {len(tasks)} tasks total, {open_n} open -> {constants.TASKS_VIEW}")


def cmd_create(args) -> None:
    ev = append_event({
        "kind": "create",
        "actor": args.actor,
        "payload": {"title": args.title, "domain": args.domain,
                    "due_date": args.due, "code": next_code(args.prefix)},
    })
    print(f"created {ev['payload']['code']} ({ev['task_id']})")
    cmd_rebuild(args)


def cmd_event(args) -> None:
    tasks = replay()
    ev = append_event({
        "kind": args.kind,
        "task_id": resolve_code(args.code, tasks),
        "actor": args.actor,
        "payload": json.loads(args.payload),
    })
    print(f"appended {ev['kind']} on {args.code}")
    cmd_rebuild(args)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--actor", required=True,
                   help="'user' solo si lo dijo Armando; si no, 'system:<rutina>'")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("create")
    c.add_argument("--title", required=True)
    c.add_argument("--prefix", default="T", choices=sorted(constants.CODE_PREFIXES),
                   help="T=tarea, A=acción que te requiere, P=propuesta")
    c.add_argument("--domain", required=True, choices=sorted(constants.DOMAIN_SLUGS))
    c.add_argument("--due")
    c.set_defaults(fn=cmd_create)
    e = sub.add_parser("event")
    e.add_argument("--code", required=True)
    e.add_argument("--kind", required=True, choices=sorted(constants.EVENT_KINDS - {"create"}))
    e.add_argument("--payload", default="{}")
    e.set_defaults(fn=cmd_event)
    sub.add_parser("rebuild").set_defaults(fn=cmd_rebuild)
    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
