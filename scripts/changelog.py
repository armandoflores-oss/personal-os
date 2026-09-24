#!/usr/bin/env python3
"""Append what the brain learned today to memory/changelog.md.

Deliberately NOT a weekly learning report. Armando said no, and he is right:
a report is homework that arrives whether or not anyone wants it, and the ones
nobody reads still cost the trust of everything around them. A changelog is the
opposite — it sits there, appends itself, and is available to whoever chooses
to look. No notification, no summary in the brief, no ceremony.

Idempotent per day: re-running rewrites today's entry in place instead of
stacking duplicates.
"""
import datetime
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib import constants  # noqa: E402

CHANGELOG = constants.MEMORY_ROOT / "changelog.md"
CABECERA = """---
titulo: Changelog del cerebro
no_weave: true
---

# Changelog

_Lo que la memoria fue aprendiendo, día por día. Se escribe solo. No es un
reporte: nadie tiene que leerlo, y nunca va a aparecer en el brief pidiendo
atención. Está aquí por si algún día quieres ver cómo creció._

"""


def contar():
    d = {}
    for folder in ("projects", "rules", "context", "people", "topics", "sources"):
        p = constants.MEMORY_ROOT / folder
        d[folder] = len([f for f in p.glob("*.md") if f.name != "CLAUDE.md"]) if p.exists() else 0
    return d


def nuevas_hoy(hoy):
    """Cards que git ve como agregadas hoy. Lo que git no registró, no pasó."""
    r = subprocess.run(["git", "log", "--since", f"{hoy} 00:00", "--diff-filter=A",
                        "--name-only", "--pretty=format:"],
                       capture_output=True, text=True, cwd=constants.REPO_ROOT)
    out = []
    for linea in r.stdout.splitlines():
        if linea.startswith("memory/") and linea.endswith(".md") and "CLAUDE.md" not in linea:
            carpeta = linea.split("/")[1]
            slug = pathlib.Path(linea).stem
            if carpeta in ("projects", "rules", "context", "people", "sources"):
                out.append((carpeta, slug))
    return sorted(set(out))


def main():
    hoy = datetime.date.today().isoformat()
    c = contar()
    nuevas = nuevas_hoy(hoy)
    if not nuevas:
        linea_nuevas = "  - Sin cards nuevas."
    else:
        por_carpeta = {}
        for carpeta, slug in nuevas:
            por_carpeta.setdefault(carpeta, []).append(slug)
        # git recuerda el nombre con el que nació la card; si después se
        # renombró, ese wikilink apunta a nada. Solo se enlaza lo que existe hoy.
        existe = {f.stem for d in constants.MEMORY_ROOT.iterdir() if d.is_dir()
                  for f in d.glob("*.md")}
        linea_nuevas = "\n".join(
            f"  - **{k}**: " + ", ".join(f"[[{s}]]" if s in existe else s for s in v[:8])
            + (f" _y {len(v)-8} más_" if len(v) > 8 else "")
            for k, v in sorted(por_carpeta.items()))

    entrada = (f"## {hoy}\n\n"
               f"  - Tamaño: {c['projects']} proyectos · {c['rules']} reglas · "
               f"{c['context']} contexto · {c['people']} gente · {c['sources']} fuentes\n"
               f"{linea_nuevas}\n")

    texto = CHANGELOG.read_text() if CHANGELOG.exists() else CABECERA
    if f"## {hoy}" in texto:
        texto = re.sub(rf"## {re.escape(hoy)}\n.*?(?=\n## |\Z)", entrada, texto, flags=re.S)
    else:
        cuerpo = texto[len(CABECERA):] if texto.startswith(CABECERA) else texto
        texto = CABECERA + entrada + "\n" + cuerpo.lstrip()
    CHANGELOG.write_text(texto, encoding="utf-8")
    print(f"changelog: {hoy} · {len(nuevas)} cards nuevas")


if __name__ == "__main__":
    main()
