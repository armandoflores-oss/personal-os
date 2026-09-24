#!/usr/bin/env python3
"""The weekly pass: promote recurring corrections, and upgrade by risk.

Two jobs that share a week's worth of evidence:

* **Corrections that repeat are a rule waiting to be written.** Saying the same
  thing three times is Armando doing by hand what the system should do by
  itself. Each promotion is ONE commit, so any single rule can be reverted
  without dragging the others with it.
* **Upgrades split by risk, and the split is mechanical.** Low risk means a
  number inside the loop's own scripts, on an allowlist, changed by regex —
  those apply themselves and show up as receipts. Everything else is
  structural and becomes a numbered proposal in the brief. Nothing is ever
  parked in a folder Armando has to remember to open.

  weekly.py cluster [--dias 7]
  weekly.py promote --reglas <archivo.json>      (un commit por regla)
  weekly.py upgrade --propuestas <archivo.json>
"""
import argparse
import datetime
import json
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib import constants, gate  # noqa: E402
from lib.feedback import read_feedback  # noqa: E402
from lib.slugs import slug_corto  # noqa: E402

LOOP = constants.REPO_ROOT / "state" / "loop"
SYNCS = constants.REPO_ROOT / "syncs"
REGLAS = constants.MEMORY_ROOT / "rules"
INSTRUCCION = pathlib.Path.home() / ".claude" / "CLAUDE.md"

# Números que el loop puede cambiarse a sí mismo. Nada fuera de esta lista, y
# nada fuera de loop.py: un "ajuste de umbral" que pueda tocar el renderizador
# del brief o los permisos no es bajo riesgo, es estructural con otro nombre.
AJUSTABLES = {
    "MAX_MUTACIONES": (1, 12),
    "VENTANA_PROPUESTA_H": (24, 168),
}
ARCHIVO_AJUSTABLE = constants.REPO_ROOT / "scripts" / "loop.py"


def tokens(t):
    """Raíces de 5 letras, no palabras completas: "correos" y "correo" son la
    misma idea, y un agrupador que no lo vea parte en dos lo que es un racimo."""
    return {w[:5] for w in gate.norm(t).split() if len(w) > 4}


def cmd_cluster(args):
    desde = (datetime.date.today() - datetime.timedelta(days=args.dias)).isoformat()
    corr = [e for e in read_feedback()
            if e["kind"] == "correction" and e["ts"][:10] >= desde and not e.get("firewalled")]
    items = [{"ts": e["ts"][:10], "texto": (e.get("lesson") or e.get("text") or "")} for e in corr]

    # Agrupación de enlace simple por solapamiento de tokens distintivos.
    grupos = []
    for it in items:
        tk = tokens(it["texto"])
        for g in grupos:
            if any(len(tk & tokens(x["texto"])) >= 3 for x in g):
                g.append(it); break
        else:
            grupos.append([it])

    racimos = [g for g in grupos if len(g) >= 2]
    sueltas = [g[0] for g in grupos if len(g) == 1]
    out = {"desde": desde, "correcciones": len(items),
           "racimos": [{"n": len(g), "textos": [x["texto"][:160] for x in g]} for g in racimos],
           "sueltas": [x["texto"][:160] for x in sueltas]}
    LOOP.mkdir(parents=True, exist_ok=True)
    (LOOP / f"racimos-{datetime.date.today().isoformat()}.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1))
    print(json.dumps(out, ensure_ascii=False, indent=1))


def git(*a):
    return subprocess.run(["git", "-C", str(constants.REPO_ROOT), *a],
                          capture_output=True, text=True)


def cmd_promote(args):
    """Una regla por commit. Revertir una no debe arrastrar a las demás."""
    reglas = json.loads(pathlib.Path(args.reglas).read_text()).get("reglas", [])
    hechas, saltadas = [], []
    for r in reglas:
        titulo, cuerpo = r.get("titulo", "").strip(), r.get("cuerpo", "").strip()
        destino = r.get("destino", "rules")
        if not titulo or not cuerpo:
            saltadas.append({"titulo": titulo, "por": "sin título o sin cuerpo"}); continue
        if destino == "instruccion":
            texto = INSTRUCCION.read_text()
            marca = f"<!-- regla-semanal: {slug_corto(titulo)} -->"
            if marca in texto:
                saltadas.append({"titulo": titulo, "por": "ya estaba en la instrucción"}); continue
            INSTRUCCION.write_text(texto.rstrip() + f"\n\n## {titulo}\n{marca}\n\n{cuerpo}\n")
            (constants.REPO_ROOT / "docs" / "instruccion-captura.md").write_text(INSTRUCCION.read_text())
            ruta = "docs/instruccion-captura.md"
        else:
            slug = slug_corto(titulo)
            f = REGLAS / f"{slug}.md"
            if f.exists():
                saltadas.append({"titulo": titulo, "por": "ya existe esa regla"}); continue
            f.write_text(f"---\ntitulo: {titulo}\npromovida: {datetime.date.today()}\n---\n\n"
                         f"# {titulo}\n\n{cuerpo}\n\n_Promovida por el pase semanal desde "
                         f"{r.get('veces', '?')} correcciones repetidas._\n", encoding="utf-8")
            ruta = f"memory/rules/{slug}.md"
        git("add", "-A")
        msg = (f"Promote recurring correction into a rule: {titulo}\n\n"
               f"{r.get('veces','?')} corrections this week said the same thing. One commit per\n"
               f"rule so any single promotion can be reverted on its own.\n\n"
               f"Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>")
        c = git("commit", "-m", msg)
        hechas.append({"titulo": titulo, "ruta": ruta, "commit": c.returncode == 0})
    print(json.dumps({"promovidas": hechas, "saltadas": saltadas}, ensure_ascii=False, indent=1))


def cargar_upgrades():
    f = LOOP / "upgrades.json"
    return json.loads(f.read_text()) if f.exists() else {"siguiente": 1, "abiertas": {}}


def cmd_upgrade(args):
    props = json.loads(pathlib.Path(args.propuestas).read_text()).get("mejoras", [])
    reg = cargar_upgrades()
    aplicadas, propuestas, rechazadas = [], [], []

    for m in props:
        const, valor = m.get("constante"), m.get("valor")
        # Bajo riesgo: un número de la lista, dentro de rango, en loop.py.
        if const and const in AJUSTABLES and isinstance(valor, int):
            lo, hi = AJUSTABLES[const]
            if not (lo <= valor <= hi):
                rechazadas.append({"constante": const, "por": f"fuera de rango [{lo},{hi}]"}); continue
            texto = ARCHIVO_AJUSTABLE.read_text()
            nuevo, n = re.subn(rf"^{const} = \d+", f"{const} = {valor}", texto, count=1, flags=re.M)
            if not n:
                rechazadas.append({"constante": const, "por": "no encontré la constante"}); continue
            ARCHIVO_AJUSTABLE.write_text(nuevo)
            git("add", "scripts/loop.py")
            git("commit", "-m", f"Loop self-tune: {const} -> {valor}\n\n{m.get('por','')}\n\n"
                                f"Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>")
            aplicadas.append({"constante": const, "valor": valor, "por": m.get("por", "")[:160]})
        else:
            # Estructural: nunca se aplica sola, nunca vive en una carpeta.
            n = reg["siguiente"]; reg["siguiente"] = n + 1
            reg["abiertas"][str(n)] = {"titulo": m.get("titulo", "")[:120],
                                       "por": m.get("por", "")[:300],
                                       "toca": m.get("toca", "")[:120],
                                       "propuesta": datetime.date.today().isoformat()}
            propuestas.append({"n": n, "titulo": m.get("titulo", "")[:80]})

    (LOOP / "upgrades.json").write_text(json.dumps(reg, indent=1, ensure_ascii=False) + "\n")
    recibo = {"ts": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
              "fecha": datetime.date.today().isoformat(), "leg": "semanal",
              "ajustes": aplicadas, "mejoras_propuestas": propuestas, "rechazadas": rechazadas}
    if aplicadas or propuestas or rechazadas:
        SYNCS.mkdir(exist_ok=True)
        with open(SYNCS / f"{recibo['fecha']}.ndjson", "a", encoding="utf-8") as fh:
            fh.write(json.dumps(recibo, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps(recibo, ensure_ascii=False, indent=1))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("cluster"); c.add_argument("--dias", type=int, default=7); c.set_defaults(fn=cmd_cluster)
    p = sub.add_parser("promote"); p.add_argument("--reglas", required=True); p.set_defaults(fn=cmd_promote)
    u = sub.add_parser("upgrade"); u.add_argument("--propuestas", required=True); u.set_defaults(fn=cmd_upgrade)
    args = ap.parse_args(); args.fn(args)


if __name__ == "__main__":
    main()
