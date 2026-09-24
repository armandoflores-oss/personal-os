#!/usr/bin/env python3
"""Refuse to commit a modification to anything already in memory/sources/.

Raw captured material is evidence. If a distillation turns out wrong you have
to be able to read what actually arrived, which only works if nobody — not
Armando, not a routine, not Claude — can quietly rewrite it afterwards.
Adding is fine. Changing is not. Deleting is not.
"""
import subprocess
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib import constants  # noqa: E402


def main():
    r = subprocess.run(["git", "diff", "--cached", "--name-status"],
                       capture_output=True, text=True, cwd=constants.REPO_ROOT)
    malos = []
    for linea in r.stdout.splitlines():
        partes = linea.split("\t")
        if len(partes) < 2:
            continue
        estado, ruta = partes[0], partes[-1]
        if not ruta.startswith("memory/sources/") or ruta.endswith((".gitkeep", "CLAUDE.md")):
            continue
        if estado.startswith("M"):
            malos.append((ruta, "modificado"))
        elif estado.startswith("D"):
            malos.append((ruta, "borrado"))
        elif estado.startswith("R"):
            malos.append((ruta, "renombrado"))
    if malos:
        print("COMMIT BLOQUEADO — el material crudo es inmutable:", file=sys.stderr)
        for ruta, que in malos:
            print(f"  {ruta}: {que}", file=sys.stderr)
        print("\nUna fuente se agrega una vez y no se vuelve a tocar. Si la lectura\n"
              "cambió, edita su página destilada en memory/context/, no el crudo.",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
