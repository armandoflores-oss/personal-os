#!/usr/bin/env python3
"""The daily brief. A renderer, not a prompt.

It reads ONLY this repository. Anything from outside — today's calendar — must
have been deposited into cache/ by the routine before this runs. That boundary
is the point: a brief assembled by a model reasoning about the day drifts,
skips its own cross-checks, and cannot be diffed. This can be re-run on any day
and produces the same bytes from the same repo.

  brief.py render                 -> stdout + briefs/YYYY-MM-DD.md
  brief.py render --dry-run       -> stdout only, no watermark move
"""
import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import constants, gate  # noqa: E402
from lib.feedback import read_feedback  # noqa: E402
from lib.replay import replay  # noqa: E402

MX = timezone(timedelta(hours=-6))          # America/Mexico_City, no DST since 2022

# Hardcoded rather than locale-dependent: the es_MX locale is not guaranteed on
# every machine this may run on, and a brief that silently switches language is
# worse than one that never had the option.
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
BRIEFS = constants.REPO_ROOT / "briefs"
CACHE = constants.REPO_ROOT / "cache"
SYNCS = constants.REPO_ROOT / "syncs"
STATE = constants.REPO_ROOT / "state"
LAST_RUN = STATE / "brief-last-run.json"

# Armando's hard rule (memory/rules/brief-maximo-dos-lineas-por-item.md): no item
# exceeds two lines. Enforced here, in the renderer, because a rule that lives
# only in an instruction erodes the first time an item has a lot to say.
WIDTH = 96
MAX_LINES = 2


def cap(text: str) -> str:
    """Fold to at most two lines of WIDTH, eliding the rest."""
    words, lines, cur = str(text).split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > WIDTH:
            lines.append(cur)
            cur = w
            if len(lines) == MAX_LINES:
                break
        else:
            cur = f"{cur} {w}".strip()
    if len(lines) < MAX_LINES and cur:
        lines.append(cur)
    out = "\n  ".join(lines[:MAX_LINES])
    consumed = sum(len(l.split()) for l in lines[:MAX_LINES])
    return out + (" …" if consumed < len(words) else "")


def last_run() -> str:
    if LAST_RUN.exists():
        return json.loads(LAST_RUN.read_text()).get("ts", "")
    return ""


def set_last_run(ts: str) -> None:
    STATE.mkdir(parents=True, exist_ok=True)
    LAST_RUN.write_text(json.dumps({"ts": ts}, indent=1) + "\n")


# --- section 1: health ----------------------------------------------------

def health(now) -> list:
    """Only speaks when something is broken. Silence is the healthy state."""
    problems = []
    wm = STATE / "watermarks.json"
    if not wm.exists():
        problems.append("La ingesta nunca ha corrido: no hay marcas de agua.")
    else:
        marks = json.loads(wm.read_text())
        for source, ts in marks.items():
            try:
                age = now - datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except ValueError:
                problems.append(f"Marca de agua ilegible en {source}: {ts!r}.")
                continue
            if age > timedelta(hours=36):
                problems.append(f"{source}: sin datos nuevos desde hace {age.days} día(s).")
    today_sync = SYNCS / f"{now.date().isoformat()}.ndjson"
    yday_sync = SYNCS / f"{(now.date() - timedelta(days=1)).isoformat()}.ndjson"
    if not today_sync.exists() and not yday_sync.exists():
        problems.append("Sin recibos de ingesta en 48h: la rutina no está corriendo.")
    for line in _receipts(now, hours=24):
        if line.get("leg") == "error":
            problems.append(f"Conector {line.get('source')} falló: {line.get('error','')[:60]}")
    return problems


# --- section 2: calendar --------------------------------------------------

def calendar_today(now):
    f = CACHE / "calendar" / f"{now.date().isoformat()}.json"
    if not f.exists():
        return None
    return json.loads(f.read_text())


def prep_notes(event) -> list:
    """Deterministic prep: memory cards whose slug matches an attendee or a
    distinctive word of the title. No inference, just the library."""
    hits, seen = [], set()
    blob = gate.norm(f"{event.get('summary','')} {' '.join(event.get('attendees', []))}")
    tokens = {t for t in blob.replace("@", " ").replace(".", " ").split() if len(t) > 4}
    for folder in ("people", "projects", "context", "rules"):
        d = constants.MEMORY_ROOT / folder
        if not d.exists():
            continue
        for card in sorted(d.glob("*.md")):
            if card.name == "CLAUDE.md":
                continue
            slug_words = {w for w in card.stem.split("-") if len(w) > 4}
            if slug_words & tokens and card.name not in seen:
                seen.add(card.name)
                hits.append(f"memory/{folder}/{card.name}")
    return hits[:3]


# --- sections 3 & 4: tasks -----------------------------------------------

def open_items():
    out = []
    for t in replay().values():
        if t["status"] != "open" or t["archived"]:
            continue
        out.append(t)
    return out


def by_domain(items):
    order = {slug: i for i, (slug, _) in enumerate(constants.DOMAINS)}
    grouped = {}
    for t in items:
        grouped.setdefault(t["domain"], []).append(t)
    for slug in sorted(grouped, key=lambda s: order.get(s, 99)):
        grouped[slug].sort(key=lambda t: (t["due_date"] or "9999", t["code"]))
        yield slug, grouped[slug]


def recent_meeting_blob(now, days=3) -> str:
    """Everything the transcripts said recently, as one lowercase haystack."""
    blob = []
    d = CACHE / "transcripts"
    if d.exists():
        for f in sorted(d.glob("*.txt")):
            try:
                age = now - datetime.fromtimestamp(f.stat().st_mtime, timezone.utc)
            except OSError:
                continue
            if age <= timedelta(days=days):
                blob.append(f.read_text(errors="ignore"))
    return gate.norm(" ".join(blob))


def closed_by_feedback_blob() -> str:
    """What Armando has said. If he told us something was done, it is done."""
    said = []
    for ev in read_feedback():
        if ev["kind"] in ("action", "status") and not ev.get("firewalled"):
            said.append(f"{ev.get('text','')} {ev.get('lesson') or ''}")
    return gate.norm(" ".join(said))


def cross_check(item, others, meetings, said):
    """Three suppressions, in the order Armando named them. Returns '' to keep."""
    dup = gate.is_duplicate(item.get("action"), item.get("counterparty"),
                            [o for o in others if o["task_id"] != item["task_id"]])
    if dup:
        return f"ya cubierto por {dup}"
    tokens = {w for w in gate.norm(item["title"]).split() if len(w) > 4}
    if len(tokens) >= 2:
        if len([t for t in tokens if t in meetings]) >= 2:
            return "ya se trató en una junta reciente"
        if len([t for t in tokens if t in said]) >= 2:
            return "ya me dijiste que estaba cerrado"
    return ""


# --- section 5: receipts --------------------------------------------------

def _receipts(now, hours=24):
    out = []
    for delta in (0, 1):
        f = SYNCS / f"{(now.date() - timedelta(days=delta)).isoformat()}.ndjson"
        if not f.exists():
            continue
        for line in f.read_text().splitlines():
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            try:
                if now - datetime.fromisoformat(rec["ts"]) <= timedelta(hours=hours):
                    out.append(rec)
            except (KeyError, ValueError):
                continue
    return out


def noise_counts(now, hours=24):
    """Counted, never listed. Noise that gets rendered stops being noise."""
    counts, f = {}, STATE / "suppressed.ndjson"
    if f.exists():
        for line in f.read_text().splitlines():
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
                if now - datetime.fromisoformat(rec["ts"]) > timedelta(hours=hours):
                    continue
            except (json.JSONDecodeError, KeyError, ValueError):
                continue
            counts[rec.get("reason", "?")] = counts.get(rec.get("reason", "?"), 0) + 1
    fw = sum(1 for t in replay().values()
             if t["domain"] in constants.FIREWALLED_DOMAINS and t["status"] == "open")
    if fw:
        counts["firewalled (retenidos)"] = fw
    return counts


# --- render ---------------------------------------------------------------

def render(now, since):
    L = []
    day = now.astimezone(MX)
    L.append(f"# Brief · {DIAS[day.weekday()]} {day.day} de {MESES[day.month - 1]} de {day.year}")
    L.append("")

    problems = health(now)
    if problems:
        L.append("## ⚠️ Salud del sistema")
        for p in problems:
            L.append(f"- {cap(p)}")
        L.append("")

    L.append("## Hoy")
    cal = calendar_today(now)
    if cal is None:
        L.append("- _Sin calendario en cache: la rutina no lo depositó._")
    elif not cal:
        L.append("- Sin eventos.")
    else:
        for ev in cal:
            who = ", ".join(a.split("@")[0] for a in ev.get("attendees", [])[:4])
            L.append(f"- **{ev.get('start','')}** {cap(ev.get('summary',''))}" + (f" · {who}" if who else ""))
            for note in prep_notes(ev):
                L.append(f"  ↳ prep: {note}")
    L.append("")

    items = open_items()
    fresh = [t for t in items if since and t["created"] > since]

    # Decide the "new" section FIRST. Anything new that the cross-check
    # suppresses has to fall back into the standing list, or a real open task
    # disappears from the brief entirely — silently, which is the worst kind.
    meetings, said = recent_meeting_blob(now), closed_by_feedback_blob()
    new_lines, suppressed, shown_new = [], 0, []
    for t in fresh:
        if t["domain"] in constants.FIREWALLED_DOMAINS:
            suppressed += 1
            continue
        why = cross_check(t, items, meetings, said)
        if why:
            suppressed += 1
            continue
        due = f" · vence {t['due_date']}" if t["due_date"] else ""
        new_lines.append(f"- **{t['code']}** {cap(t['title'])}{due}")
        shown_new.append(t["task_id"])
    standing = [t for t in items if t["task_id"] not in shown_new]

    L.append("## Pendientes abiertos")
    if not standing:
        L.append("- Nada abierto.")
    for slug, group in by_domain(standing):
        if slug in constants.FIREWALLED_DOMAINS:
            continue
        label = dict(constants.DOMAINS)[slug]
        L.append(f"### {label}")
        for t in group:
            due = f" · vence {t['due_date']}" if t["due_date"] else ""
            wait = f" · esperando a {t['waiting_on']}" if t["waiting_on"] else ""
            L.append(f"- **{t['code']}** {cap(t['title'])}{due}{wait}")
    L.append("")

    L.append("## Nuevo que te requiere")
    L.extend(new_lines)
    if not new_lines:
        L.append("- Nada nuevo." + (f" ({suppressed} suprimido(s) por el cruce; siguen arriba)" if suppressed else ""))
    elif suppressed:
        L.append(f"- _{suppressed} más suprimido(s) por el cruce; siguen en pendientes._")
    L.append("")

    L.append("## Lo que hice mientras no estabas")
    recs = _receipts(now)
    if not recs:
        L.append("- Nada que reportar.")
    for r in recs:
        if r.get("leg") == "inbound":
            for c in r.get("creados", []):
                L.append(f"- **{c['code']}** creada desde {r['source']} · {cap(c['title'])}")
        elif r.get("leg") == "outbound":
            for c in r.get("cerrados", []):
                L.append(f"- **{c['code']}** cerrada · evidencia: {cap(c['evidencia'])}")
        elif r.get("leg") == "error":
            L.append(f"- ⚠️ {r.get('source')} falló · {cap(r.get('error',''))}")
    L.append("")

    counts = noise_counts(now)
    L.append("## Ruido")
    if not counts:
        L.append("- Ninguno.")
    else:
        L.append("- " + " · ".join(f"{v} {k}" for k, v in sorted(counts.items())))
    L.append("")
    L.append("_Responde con el código: `T-4 listo` · `T-4 viernes` · `T-4 qué` · `reply.py forms` para las diez._")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("render")
    r.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    now = datetime.now(timezone.utc)
    text = render(now, last_run())
    print(text)
    if not args.dry_run:
        BRIEFS.mkdir(parents=True, exist_ok=True)
        (BRIEFS / f"{now.astimezone(MX).date().isoformat()}.md").write_text(text + "\n")
        set_last_run(now.isoformat(timespec="seconds"))


if __name__ == "__main__":
    main()
