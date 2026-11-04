#!/usr/bin/env python3
"""Convierte el brief del día en una página HTML, determinista.

Por qué existe: el brief vivía en la respuesta de una sesión de rutina, y una
sesión es una fila más en una lista de filas parecidas — cinco ingestas al día
más el brief más el loop. Armando dijo tres veces que no lo encontraba.
Titularla con la fecha y marcarla no leída no alcanzó. Una página con URL fija,
que se reescribe en su lugar cada mañana, es UN lugar y no se multiplica.

Lo rinde un script y no el modelo, por la misma razón que brief.py: un brief
redactado a mano se ve igual de bien, se salta los tres cruces de supresión, y
desde ese momento hay dos versiones de la verdad. Aquí no se interpreta nada:
se traduce el markdown que brief.py ya escribió.

  brief_html.py                   -> cache/brief.html (el .md más reciente)
  brief_html.py --fecha 2026-11-04
"""
import argparse
import html
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib import constants  # noqa: E402

BRIEFS = constants.REPO_ROOT / "briefs"
SALIDA = constants.REPO_ROOT / "cache" / "brief.html"

# Los códigos son el vocabulario con el que Armando contesta: T- tarea,
# A- acción, P- propuesta. Se marcan en la página porque son lo accionable.
CODIGO = re.compile(r"\b((?:T|A|P)-\d+)\b")


def en_linea(texto: str) -> str:
    """Markdown en línea -> HTML. Escapa primero: el brief trae asuntos de
    correo con < > & que no son marcado."""
    t = html.escape(texto)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\w*])_([^_]+)_(?![\w*])", r"<em>\1</em>", t)
    return CODIGO.sub(r'<span class="codigo">\1</span>', t)


def rinde(md: str) -> tuple[str, str]:
    """Devuelve (titulo, cuerpo_html). Un traductor de líneas, sin estado
    escondido: cada forma que brief.py emite tiene aquí su rama."""
    titulo, partes = "Brief", []
    seccion = None          # clase de la sección abierta, para el estilo
    lista_abierta = False

    def cierra_lista():
        nonlocal lista_abierta
        if lista_abierta:
            partes.append("</ul>")
            lista_abierta = False

    for linea in md.splitlines():
        cruda = linea.rstrip()
        if not cruda.strip():
            continue

        if cruda.startswith("# "):
            titulo = cruda[2:].strip()
            continue

        if cruda.startswith("## "):
            cierra_lista()
            nombre = cruda[3:].strip()
            seccion = "salud" if "Salud" in nombre else "normal"
            partes.append(f'</section><section class="{seccion}">'
                          f"<h2>{en_linea(nombre)}</h2>")
            continue

        if cruda.startswith("### "):
            cierra_lista()
            partes.append(f"<h3>{en_linea(cruda[4:].strip())}</h3>")
            continue

        # La continuación de un item: brief.py parte en dos líneas de 96 y
        # sangra la segunda con dos espacios. Es el mismo item, no uno nuevo.
        if cruda.startswith("  ") and not cruda.lstrip().startswith(("-", "↳")):
            if lista_abierta:
                partes.append(" " + en_linea(cruda.strip()))
                continue

        # Las líneas de preparación de junta: contexto de la wiki, subordinado
        # al evento, nunca accionable por sí mismo.
        if cruda.lstrip().startswith("↳"):
            if lista_abierta:
                partes.append(f'<span class="prep">{en_linea(cruda.lstrip()[1:].strip())}</span>')
            continue

        if cruda.startswith("- "):
            if not lista_abierta:
                partes.append("<ul>")
                lista_abierta = True
            else:
                partes.append("</li>")
            partes.append(f"<li>{en_linea(cruda[2:].strip())}")
            continue

        # Línea suelta en cursiva: las notas y el pie de formas de respuesta.
        cierra_lista()
        partes.append(f'<p class="nota">{en_linea(cruda.strip())}</p>')

    cierra_lista()
    cuerpo = "".join(partes)
    if lista_abierta or "<li>" in cuerpo:
        cuerpo = cuerpo.replace("</ul>", "</li></ul>")
    # La primera sección abre sin que nada la haya cerrado.
    return titulo, cuerpo.removeprefix("</section>") + "</section>"


PAGINA = """<title>Brief diario</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;1,400&family=IBM+Plex+Mono:wght@500;600&display=swap">
<style>
/* Una columna de lectura; los códigos y las horas en mono para que alineen. */
:root {
  --papel: #f7f8f8;
  --tarjeta: #ffffff;
  --tinta: #16201f;
  --tenue: #5d6b69;
  --linea: #dde3e2;
  --acento: #0f6b63;
  --ambar: #8a5a00;
  --ambar-fondo: #fdf4e3;
  --sans: "IBM Plex Sans", ui-sans-serif, system-ui, sans-serif;
  --mono: "IBM Plex Mono", ui-monospace, "SF Mono", monospace;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --papel: #101413; --tarjeta: #171d1c; --tinta: #e7edec; --tenue: #94a3a1;
    --linea: #2a3332; --acento: #52bdb1; --ambar: #e0ac5c; --ambar-fondo: #241c0e;
    color-scheme: dark;
  }
}
:root[data-theme="dark"] {
  --papel: #101413; --tarjeta: #171d1c; --tinta: #e7edec; --tenue: #94a3a1;
  --linea: #2a3332; --acento: #52bdb1; --ambar: #e0ac5c; --ambar-fondo: #241c0e;
  color-scheme: dark;
}
body {
  background: var(--papel);
  color: var(--tinta);
  font-family: var(--sans);
  font-size: 15px;
  line-height: 1.55;
}
.hoja {
  max-width: 44rem;
  margin: 0 auto;
  padding-left: max(16px, env(safe-area-inset-left, 0px));
  padding-right: max(16px, env(safe-area-inset-right, 0px));
  padding-block: 2.5rem 4rem;
}
h1 {
  font-size: 1.45rem;
  font-weight: 600;
  letter-spacing: -0.015em;
  text-wrap: balance;
  margin: 0 0 0.35rem;
}
.sello {
  font-family: var(--mono);
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--tenue);
  margin: 0 0 2rem;
}
section { margin-block: 0 1.9rem; }
h2 {
  font-size: 0.72rem;
  font-weight: 600;
  font-family: var(--mono);
  text-transform: uppercase;
  letter-spacing: 0.11em;
  color: var(--acento);
  padding-bottom: 0.45rem;
  border-bottom: 1px solid var(--linea);
  margin: 0 0 0.9rem;
}
h3 {
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--tenue);
  margin: 1.1rem 0 0.4rem;
}
ul { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 0.6rem; }
li {
  min-width: 0;
  background: var(--tarjeta);
  border: 1px solid var(--linea);
  border-radius: 6px;
  padding: 0.6rem 0.75rem;
  overflow-wrap: anywhere;
}
.codigo {
  font-family: var(--mono);
  font-size: 0.82em;
  font-weight: 600;
  color: var(--acento);
  font-variant-numeric: tabular-nums;
}
li strong { font-weight: 600; }
.prep {
  display: block;
  font-size: 0.86rem;
  color: var(--tenue);
  border-left: 2px solid var(--linea);
  padding-left: 0.6rem;
  margin-top: 0.4rem;
}
/* La salud es lo único que cambia de color: el brief la muestra solo cuando
   algo no está verde, así que su presencia ya es la señal. */
.salud li {
  background: var(--ambar-fondo);
  border-color: color-mix(in srgb, var(--ambar) 35%, transparent);
}
.salud .codigo, .salud strong { color: var(--ambar); }
.nota { color: var(--tenue); font-size: 0.86rem; margin: 0.7rem 0 0; }
code {
  font-family: var(--mono);
  font-size: 0.85em;
  background: color-mix(in srgb, var(--tinta) 7%, transparent);
  padding: 0.1em 0.3em;
  border-radius: 3px;
}
</style>
<main class="hoja">
<h1>__TITULO__</h1>
<p class="sello">__SELLO__</p>
__CUERPO__
</main>
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fecha", help="YYYY-MM-DD; por omisión el brief más reciente")
    args = ap.parse_args()

    if args.fecha:
        f = BRIEFS / f"{args.fecha}.md"
    else:
        disponibles = sorted(BRIEFS.glob("20*.md"))
        if not disponibles:
            raise SystemExit("no hay ningún brief rendido todavía")
        f = disponibles[-1]
    if not f.exists():
        raise SystemExit(f"no existe {f}")

    titulo, cuerpo = rinde(f.read_text())
    pagina = (PAGINA.replace("__TITULO__", html.escape(titulo))
                    .replace("__SELLO__", f"rendido por brief.py · {f.stem}")
                    .replace("__CUERPO__", cuerpo))
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(pagina)
    print(SALIDA)


if __name__ == "__main__":
    main()
