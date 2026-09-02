#!/usr/bin/env python3
"""Phase 2 CLI — feedback capture.

The instruction decides WHAT is a signal. This script does every write and
renders the receipt, so the receipt is a view over the append-only logs and
cannot describe a write that did not happen (rules 7 and 8).

  capture.py mark                      -> timestamp opening a turn
  capture.py signal --kind ... --text ...
  capture.py receipt --since <ts>      -> the block to paste at the end of a reply
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import constants, events, feedback, replay  # noqa: E402

LABEL = {
    "correction": "corrección",
    "fact": "hecho",
    "status": "estatus",
    "contact": "contacto",
    "commitment": "compromiso",
    "action": "acción",
}


def cmd_mark(args):
    print(datetime.now(timezone.utc).isoformat(timespec="seconds"))


def cmd_signal(args):
    card_rel = None
    created = False
    fw = bool(args.domain and args.domain in constants.FIREWALLED_DOMAINS)

    if args.kind in constants.CARD_FOLDER and not args.no_card:
        title = args.card_title or args.lesson or args.text
        card_rel = args.card or feedback.card_path(args.kind, title, args.domain)
        line = args.lesson or args.text
        card_rel, created = feedback.write_card(
            card_rel, args.card_title or title[:80], line, source=f"feedback:{args.kind}")

    ev = feedback.append_feedback(
        args.kind, args.text, lesson=args.lesson, card=card_rel,
        domain=args.domain, code=args.code, actor=args.actor)

    if fw:
        print(f"señal {args.kind} registrada (firewalled — sin detalle)", file=sys.stderr)
    else:
        print(f"{ev['id']} {args.kind} -> feedback.ndjson"
              + (f" · {card_rel}{' (nueva)' if created else ''}" if card_rel else ""), file=sys.stderr)


def _task_codes():
    try:
        return {tid: t for tid, t in replay.replay().items()}
    except (FileNotFoundError, ValueError):
        return {}


def cmd_receipt(args):
    since = args.since
    tasks = _task_codes()
    lines, withheld = [], 0

    for ev in feedback.read_feedback():
        if ev["ts"] < since:
            continue
        if ev.get("firewalled"):
            withheld += 1
            continue
        label = LABEL.get(ev["kind"], ev["kind"])
        if ev.get("card"):
            detail = f"→ {ev['card']}"
            if ev.get("lesson"):
                detail += f" · «{ev['lesson']}»"
        else:
            detail = f"→ feedback.ndjson · «{ev.get('lesson') or ev['text'][:70]}»"
        lines.append(f"· {label} {detail}")

    try:
        task_evs = events.read_events()
    except FileNotFoundError:
        task_evs = []
    for ev in task_evs:
        if ev["ts"] < since:
            continue
        t = tasks.get(ev["task_id"], {})
        if t.get("domain") in constants.FIREWALLED_DOMAINS:
            withheld += 1
            continue
        code = t.get("code", ev["task_id"][:6])
        p = ev.get("payload", {})
        if ev["kind"] == "create":
            what = f"nueva · {p.get('title', '')[:60]}"
        elif ev["kind"] == "set_status":
            what = f"→ {p.get('status')}"
        elif ev["kind"] == "archive":
            what = "→ archivada"
        elif ev["kind"] == "snooze":
            what = f"→ pospuesta a {p.get('until')}"
        else:
            what = f"→ {ev['kind']}"
        lines.append(f"· acción {code} {what} · tasks.ndjson")

    if withheld:
        lines.append(f"· {withheld} señal(es) retenida(s) — dominio firewalled")

    if not lines:
        return  # Nothing captured: print nothing. A receipt is never decorative.
    print("─ capturado ─")
    for ln in lines:
        print(ln)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("mark").set_defaults(func=cmd_mark)

    s = sub.add_parser("signal")
    s.add_argument("--kind", required=True, choices=sorted(constants.FEEDBACK_KINDS))
    s.add_argument("--text", required=True, help="Armando's own words, verbatim")
    s.add_argument("--lesson", help="the durable line written to the card")
    s.add_argument("--card", help="explicit card path; otherwise derived")
    s.add_argument("--card-title", help="human title for a new card")
    s.add_argument("--domain", choices=sorted(constants.DOMAIN_SLUGS))
    s.add_argument("--code", help="related task code, e.g. T-4")
    s.add_argument("--actor", default="user")
    s.add_argument("--no-card", action="store_true", help="log the signal only")
    s.set_defaults(func=cmd_signal)

    r = sub.add_parser("receipt")
    r.add_argument("--since", required=True)
    r.set_defaults(func=cmd_receipt)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
