#!/usr/bin/env python3
"""Ingest CLI — the deterministic half of the cloud routine.

The routine's prompt does exactly one thing a script cannot: call the
connectors and hand over raw items as JSON. Every judgement after that
happens here, where it is testable and where a change is a commit.

  ingest.py watermark --source gmail                 -> last cursor, or ""
  ingest.py run --source gmail --items items.json    -> gate, dedupe, create
  ingest.py reconcile --sent sent.json               -> close what was answered
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import constants, gate  # noqa: E402
from lib.codes import next_code  # noqa: E402
from lib.events import append_event  # noqa: E402
from lib.replay import replay  # noqa: E402

WATERMARKS = constants.REPO_ROOT / "state" / "watermarks.json"
SUPPRESSED = constants.REPO_ROOT / "state" / "suppressed.ndjson"
SYNCS = constants.REPO_ROOT / "syncs"

# Per-run ceiling. A connector that suddenly returns a year of history must not
# be able to mint a hundred tasks; it should hit the cap and say so.
MAX_CREATES_PER_RUN = 12


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_watermarks() -> dict:
    if WATERMARKS.exists():
        return json.loads(WATERMARKS.read_text())
    return {}


def save_watermarks(w: dict) -> None:
    WATERMARKS.parent.mkdir(parents=True, exist_ok=True)
    WATERMARKS.write_text(json.dumps(w, indent=1, sort_keys=True) + "\n")


def cmd_watermark(args):
    w = load_watermarks()
    if args.set:
        w[args.source] = args.set
        save_watermarks(w)
        print(f"{args.source} watermark = {args.set}")
    else:
        print(w.get(args.source, ""))


def log_suppression(rec: dict) -> None:
    SUPPRESSED.parent.mkdir(parents=True, exist_ok=True)
    with open(SUPPRESSED, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")


def open_task_index():
    """Open tasks decorated with the action/counterparty the gate would derive,
    so dedupe compares like with like."""
    out = []
    for t in replay().values():
        if t["status"] != "open" or t["archived"]:
            continue
        blob = f"{t['title']} {t.get('owner') or ''} {t.get('waiting_on') or ''}"
        out.append({**t,
                    "action": t.get("action") or gate.extract_action(blob),
                    "counterparty": t.get("counterparty") or gate.extract_counterparty(blob)})
    return out


def cmd_run(args):
    items = json.loads(Path(args.items).read_text())
    if isinstance(items, dict):
        items = items.get("items", [])
    watermark = load_watermarks().get(args.source, "")

    created, suppressed, skipped_old, capped = [], [], 0, 0
    index = open_task_index()
    newest = watermark

    for item in items:
        ts = item.get("ts", "")
        if watermark and ts and ts <= watermark:
            skipped_old += 1
            continue
        newest = max(newest, ts) if ts else newest

        verdict = gate.evaluate(item)
        if not verdict["accept"]:
            rec = {"ts": _now(), "source": args.source, "item_id": item.get("id"),
                   "reason": verdict["reason"], "detail": verdict.get("detail", ""),
                   "subject": (item.get("subject") or "")[:120]}
            log_suppression(rec); suppressed.append(rec)
            continue

        dup = gate.is_duplicate(verdict["action"], verdict["counterparty"], index)
        if dup:
            rec = {"ts": _now(), "source": args.source, "item_id": item.get("id"),
                   "reason": "duplicado", "detail": f"ya abierto en {dup}",
                   "action": verdict["action"], "counterparty": verdict["counterparty"],
                   "subject": (item.get("subject") or "")[:120]}
            log_suppression(rec); suppressed.append(rec)
            continue

        if len(created) >= MAX_CREATES_PER_RUN:
            capped += 1
            continue

        title = (item.get("subject") or verdict["sentence"])[:120]
        ev = append_event({
            "kind": "create", "actor": f"system:ingest:{args.source}",
            "payload": {"title": title, "domain": verdict["domain"],
                        "code": next_code("T"), "due_date": item.get("due_date"),
                        "action": verdict["action"], "counterparty": verdict["counterparty"],
                        "source": f"{args.source}:{item.get('id')}",
                        "evidence": verdict["sentence"]},
        })
        code = ev["payload"]["code"]
        created.append({"code": code, "title": title, "domain": verdict["domain"],
                        "counterparty": verdict["counterparty"], "action": verdict["action"]})
        index.append({"status": "open", "archived": False, "code": code,
                      "action": verdict["action"], "counterparty": verdict["counterparty"]})

    if newest and newest != watermark:
        w = load_watermarks(); w[args.source] = newest; save_watermarks(w)

    subprocess.run([sys.executable, str(Path(__file__).parent / "task.py"), "rebuild"],
                   check=True, capture_output=True)
    receipt = {"ts": _now(), "source": args.source, "leg": "inbound",
               "vistos": len(items), "ya_vistos": skipped_old,
               "creados": created, "suprimidos": suppressed,
               "tope_alcanzado": capped, "watermark": newest}
    write_receipt(receipt)
    print(json.dumps(receipt, ensure_ascii=False, indent=1))


def cmd_reconcile(args):
    """Outbound leg: what Armando actually sent, matched against what is open.

    Evidence bar, deliberately explicit: the counterparty must match AND at
    least two distinctive tokens of the task title must appear in what he sent.
    One token matches everything; two is the difference between evidence and
    coincidence. Reopening costs one word, so a rare wrong close is cheap.
    """
    sent = json.loads(Path(args.sent).read_text())
    if isinstance(sent, dict):
        sent = sent.get("items", [])
    closed, near = [], []

    for t in open_task_index():
        if t["domain"] in constants.FIREWALLED_DOMAINS:
            continue  # firewalled never auto-closes (rule 6)
        title_tokens = {w for w in gate.norm(t["title"]).split() if len(w) > 4}
        for msg in sent:
            blob = gate.norm(f"{msg.get('subject','')} {msg.get('text','')} "
                             f"{' '.join(msg.get('recipients', []))}")
            if t["counterparty"] not in blob:
                continue
            overlap = sorted(tok for tok in title_tokens if tok in blob)
            if len(overlap) >= 2:
                append_event({"kind": "set_status", "actor": "system:ingest:outbound",
                              "task_id": t["task_id"],
                              "payload": {"status": "done",
                                          "evidence": f"enviado {msg.get('ts','')} a "
                                                      f"{t['counterparty']}: «{(msg.get('subject') or '')[:80]}»"}})
                closed.append({"code": t["code"], "titulo": t["title"],
                               "evidencia": (msg.get("subject") or "")[:80],
                               "tokens": overlap})
                break
            if len(overlap) == 1:
                near.append({"code": t["code"], "token": overlap[0],
                             "asunto": (msg.get("subject") or "")[:80]})

    subprocess.run([sys.executable, str(Path(__file__).parent / "task.py"), "rebuild"],
                   check=True, capture_output=True)
    receipt = {"ts": _now(), "leg": "outbound", "revisados": len(sent),
               "cerrados": closed, "casi": near}
    write_receipt(receipt)
    print(json.dumps(receipt, ensure_ascii=False, indent=1))


def write_receipt(receipt: dict) -> None:
    SYNCS.mkdir(parents=True, exist_ok=True)
    day = receipt["ts"][:10]
    with open(SYNCS / f"{day}.ndjson", "a", encoding="utf-8") as f:
        f.write(json.dumps(receipt, ensure_ascii=False, sort_keys=True) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    w = sub.add_parser("watermark"); w.add_argument("--source", required=True)
    w.add_argument("--set"); w.set_defaults(func=cmd_watermark)
    r = sub.add_parser("run"); r.add_argument("--source", required=True)
    r.add_argument("--items", required=True); r.set_defaults(func=cmd_run)
    o = sub.add_parser("reconcile"); o.add_argument("--sent", required=True)
    o.set_defaults(func=cmd_reconcile)
    args = ap.parse_args(); args.func(args)


if __name__ == "__main__":
    main()
