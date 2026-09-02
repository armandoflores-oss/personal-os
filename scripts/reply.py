#!/usr/bin/env python3
"""Parse one of Armando's terse replies into events.

Ten forms, all four words or fewer. The grammar lives here in code so the
vocabulary cannot drift with a prompt, and so an unrecognised reply FAILS
LOUDLY instead of being guessed at — a misread reply writes the wrong event,
and a wrong event is worse than no event.

  reply.py parse "T-4 listo"
  reply.py forms            # print the table
"""
import argparse
import json
import re
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import constants  # noqa: E402
from lib.codes import resolve_code  # noqa: E402
from lib.events import append_event  # noqa: E402
from lib.replay import replay  # noqa: E402

CODE_RE = re.compile(r"^([TAP])-?(\d+)\b", re.I)

DONE     = {"listo", "hecho", "ya", "done", "ok", "cerrada", "cierra", "✓"}
NOT_DONE = {"no", "nel", "abierta", "reabre", "sigue", "falta", "todavia", "todavía"}
DEFER    = {"pospon", "pospón", "empuja", "mueve", "para", "al", "a"}
VETO     = {"nunca", "jamas", "jamás"}
EXPLAIN  = {"que", "qué", "cual", "cuál", "porque", "porqué", "por"}
APPLY    = {"va", "aplica", "aplícala", "aplicala", "adelante", "dale", "si", "sí"}
DROP     = {"ruido", "borra", "bórrala", "descarta"}
WAITING  = {"espera", "esperando", "bloqueada", "bloqueado", "depende"}
OWNER    = {"de", "es", "pasasela", "pásasela", "asigna", "reasigna"}
DUP      = {"dup", "duplicada", "duplicado", "repetida"}

WEEKDAYS = {"lunes": 0, "martes": 1, "miercoles": 2, "miércoles": 2, "jueves": 3,
            "viernes": 4, "sabado": 5, "sábado": 5, "domingo": 6}
MONTHS = {"ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
          "jul": 7, "ago": 8, "sep": 9, "oct": 10, "nov": 11, "dic": 12}


def parse_date(tokens):
    """Resolve a date phrase to YYYY-MM-DD. Returns None if there is none."""
    today = date.today()
    text = " ".join(tokens).lower()
    m = re.search(r"(\d{4}-\d{2}-\d{2})", text)
    if m:
        return m.group(1)
    if "manana" in text or "mañana" in text:
        return (today + timedelta(days=1)).isoformat()
    m = re.search(r"\+(\d+)\s*d", text)
    if m:
        return (today + timedelta(days=int(m.group(1)))).isoformat()
    for name, idx in WEEKDAYS.items():
        if name in text:
            ahead = (idx - today.weekday()) % 7 or 7   # always the NEXT one
            return (today + timedelta(days=ahead)).isoformat()
    m = re.search(r"(\d{1,2})\s*(ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)", text)
    if m:
        d, mo = int(m.group(1)), MONTHS[m.group(2)]
        y = today.year + (1 if mo < today.month else 0)
        return date(y, mo, d).isoformat()
    return None


def classify(code, rest):
    """Return (event_kind, payload, human_summary). Raises on anything unclear."""
    if not rest:
        raise ValueError(f"«{code}» sin verbo: no sé qué hacer. Prueba «{code} listo» o «{code} qué».")
    words = [w.lower().strip(".,;") for w in rest]
    head = words[0]
    tail = " ".join(rest[1:]).strip()

    if head in EXPLAIN:
        return "explain", {}, "explicar (solo lectura, no escribe nada)"
    if head in VETO:
        return "veto", {"reason": tail or "vetada por Armando"}, "vetada para siempre"
    if head in APPLY:
        return "apply_proposal", {}, "propuesta aplicada ya"
    if head in DUP or (len(words) > 1 and words[1] in DUP):
        m = CODE_RE.match(tail) or (CODE_RE.match(" ".join(rest[2:])) if len(rest) > 2 else None)
        target = f"{m.group(1).upper()}-{m.group(2)}" if m else "?"
        return "archive", {"reason": f"duplicada de {target}"}, f"archivada como duplicada de {target}"
    if head in DROP:
        return "archive", {"reason": "descartada por Armando: no aplica"}, "descartada"
    if head in NOT_DONE:
        if "aplica" in words:
            return "archive", {"reason": "no aplica"}, "descartada (no aplica)"
        return "set_status", {"status": "open", "evidence": "Armando dice que no está hecha"}, "reabierta"
    if head in DONE:
        return "set_status", {"status": "done", "evidence": tail or "Armando dijo que está listo"}, "cerrada"
    if head in WAITING:
        who = tail or " ".join(rest[1:])
        if not who:
            raise ValueError(f"«{code} {head}» sin destinatario: ¿esperando a quién?")
        return "set_waiting_on", {"who": who}, f"esperando a {who}"
    if head in OWNER:
        # Strip the connectors so "es de Laura" and "pásasela a Laura" both
        # store the person, not the preposition.
        who_tokens = list(rest[1:])
        while who_tokens and who_tokens[0].lower().strip(".,") in {"de", "a", "al", "para", "es"}:
            who_tokens.pop(0)
        who = " ".join(who_tokens).strip()
        if not who:
            raise ValueError(f"«{code} {head}» sin persona: ¿de quién es?")
        return "set_owner", {"owner": who}, f"reasignada a {who}"
    when = parse_date(words)
    if when or head in DEFER:
        when = when or parse_date(words[1:])
        if not when:
            raise ValueError(f"«{code} {' '.join(words)}»: no entendí la fecha.")
        return "snooze", {"until": when}, f"pospuesta a {when}"
    raise ValueError(
        f"No entendí «{code} {' '.join(rest)}». Formas válidas: reply.py forms")


def cmd_parse(args):
    raw = args.text.strip()
    m = CODE_RE.match(raw)
    if not m:
        raise SystemExit(f"«{raw}» no empieza con un código T-/A-/P-.")
    code = f"{m.group(1).upper()}-{m.group(2)}"
    rest = raw[m.end():].split()

    tasks = replay()
    task_id = resolve_code(code, tasks)   # raises loudly on 0 or >1 matches
    t = tasks[task_id]

    kind, payload, summary = classify(code, rest)

    if kind == "explain":
        print(json.dumps({
            "code": code, "titulo": t["title"], "dominio": t["domain"],
            "estatus": t["status"], "creada": t["created"], "vence": t["due_date"],
            "owner": t["owner"], "esperando": t["waiting_on"],
            "notas": t["notes"],
        }, ensure_ascii=False, indent=1))
        return

    if t["domain"] in constants.FIREWALLED_DOMAINS and not args.confirm_firewalled:
        raise SystemExit(f"{code} está en un dominio firewalled: requiere --confirm-firewalled.")

    append_event({"kind": kind, "actor": args.actor, "task_id": task_id, "payload": payload})
    subprocess.run([sys.executable, str(Path(__file__).parent / "task.py"), "rebuild"],
                   check=True, capture_output=True)
    print(f"{code} {summary}")


FORMS = [
    ("1", "T-4 listo",          "hecho · ya · ok · cerrada",        "la cierra con evidencia"),
    ("2", "T-4 no",             "sigue · falta · reabre",           "la reabre: corrige un cierre equivocado"),
    ("3", "T-4 viernes",        "mañana · 12 sep · +3d",            "la pospone a esa fecha"),
    ("4", "T-4 es de Laura",    "pásasela a Laura",                 "cambia el dueño"),
    ("5", "P-2 nunca",          "jamás",                            "veto permanente: no se vuelve a proponer"),
    ("6", "T-4 qué",            "por qué · de dónde",               "te explica: origen, evidencia, notas"),
    ("7", "T-4 espera Kavak",   "bloqueada por · depende de",       "la marca esperando a alguien"),
    ("8", "T-4 dup T-9",        "duplicada de T-9",                 "la archiva como duplicada"),
    ("9", "P-2 va",             "aplica · dale · sí",               "aplica la propuesta ya, sin esperar 72h"),
    ("10", "A-3 no aplica",     "ruido · bórrala",                  "la descarta: no era una cosa real"),
]


def cmd_forms(args):
    w = max(len(f[1]) for f in FORMS)
    print(f"{'#':>3}  {'escribes':<{w}}  {'también':<28}  qué pasa")
    for n, form, alts, effect in FORMS:
        print(f"{n:>3}  {form:<{w}}  {alts:<28}  {effect}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("parse")
    p.add_argument("text")
    p.add_argument("--actor", default="user")
    p.add_argument("--confirm-firewalled", action="store_true")
    p.set_defaults(func=cmd_parse)
    sub.add_parser("forms").set_defaults(func=cmd_forms)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
