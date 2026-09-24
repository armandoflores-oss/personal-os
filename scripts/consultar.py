#!/usr/bin/env python3
"""Consult the wiki before drafting. One command, so it actually happens.

"Check the memory first" as a sentence in an instruction gets skipped on a busy
turn and nobody notices. As a command with output you either ran it or you did
not, and what it returns goes into the draft.

  consultar.py "Fede Ranero" Penske BCA
  consultar.py --evento "Uber alignment" --asistentes fede.ranero@draiver.com,dan.rizzo@draiver.com
"""
import argparse
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib import constants  # noqa: E402

MEM = constants.MEMORY_ROOT
ORDEN = ["rules", "people", "projects", "context", "topics"]
ETIQUETA = {"rules": "REGLAS QUE APLICAN", "people": "GENTE",
            "projects": "QUÉ ESTÁ PASANDO", "context": "CONTEXTO", "topics": "HUBS"}


def norm(t):
    t = t.lower()
    for a, b in (("á","a"),("é","e"),("í","i"),("ó","o"),("ú","u"),("ñ","n")):
        t = t.replace(a, b)
    return t


def lineas_clave(texto, limite=3):
    out = []
    for l in texto.splitlines():
        l = l.strip()
        if l.startswith("- 20") and "<!--" in l:
            out.append(re.sub(r"\s*<!--.*?-->", "", l[13:]).strip())
        elif l.startswith("- ") and not l.startswith("- [["):
            out.append(l[2:].strip())
        if len(out) >= limite:
            break
    return out


def buscar(terminos):
    """Cards que mencionan cualquiera de los términos, agrupadas por carpeta."""
    pats = [re.compile(rf"(?<![\w\-]){re.escape(norm(t))}(?![\w\-])") for t in terminos if t]
    hallazgos = {k: [] for k in ORDEN}
    for folder in ORDEN:
        d = MEM / folder
        if not d.exists():
            continue
        for f in sorted(d.glob("*.md")):
            if f.name == "CLAUDE.md":
                continue
            txt = f.read_text(errors="ignore")
            if any(p.search(norm(txt)) for p in pats):
                m = re.search(r"^titulo:\s*(.+)$", txt, re.M)
                hallazgos[folder].append((f.stem, (m.group(1).strip() if m else f.stem)[:80],
                                          lineas_clave(txt)))
    return hallazgos


def imprimir(hallazgos, terminos):
    total = sum(len(v) for v in hallazgos.values())
    print(f"=== La wiki sobre: {', '.join(terminos)} — {total} cards ===")
    if not total:
        print("  Nada. No inventes contexto: redacta con lo que tengas y dilo si hace falta.")
        return
    # Las reglas primero, siempre: son restricciones, no color.
    for folder in ORDEN:
        if not hallazgos[folder]:
            continue
        print(f"\n## {ETIQUETA[folder]}")
        for slug, titulo, lineas in hallazgos[folder][:8]:
            print(f"  [{slug}] {titulo}")
            for l in lineas[:2]:
                print(f"      · {l[:150]}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("terminos", nargs="*")
    ap.add_argument("--evento")
    ap.add_argument("--asistentes", help="correos separados por coma")
    a = ap.parse_args()
    t = list(a.terminos)
    if a.evento:
        t += [w for w in re.split(r"[^\wáéíóúñ]+", a.evento) if len(w) > 3]
    if a.asistentes:
        for correo in a.asistentes.split(","):
            local = correo.split("@")[0]
            t += [p for p in local.replace(".", " ").split() if len(p) > 3]
    if not t:
        raise SystemExit("qué consulto? pasa nombres, organizaciones o temas")
    imprimir(buscar(t), t)


if __name__ == "__main__":
    main()
