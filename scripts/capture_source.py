#!/usr/bin/env python3
"""Capture lanes for outside reading: raw in, distilled out.

Two halves, deliberately separated:

* **Raw is immutable.** Whatever came in — the article text, the PDF, the note
  — lands in `memory/sources/` exactly once and is never touched again. It is
  the evidence; if the distillation is wrong you can always go back and read
  what actually arrived. The pre-commit hook refuses modifications there.
* **Distilled is living.** A page in `memory/context/` summarises it and links
  it to the people, projects and topics it touches. That one gets rewritten as
  understanding improves.

Dedupe is by content hash, so the same article captured through two different
lanes produces one source, not two.

  capture_source.py add --file <ruta> [--titulo T] [--resumen R] [--origen url]
  capture_source.py add --url <url> --texto <archivo-con-el-texto> [--resumen R]
  capture_source.py scan                 # carpeta vigilada
  capture_source.py list
"""
import argparse
import datetime
import hashlib
import json
import pathlib
import re
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib import constants  # noqa: E402
from lib.slugs import slug_corto  # noqa: E402

SOURCES = constants.MEMORY_ROOT / "sources"
DESTILADOS = constants.MEMORY_ROOT / "context"
INDICE = constants.REPO_ROOT / "state" / "sources-index.json"
VIGILADA = pathlib.Path.home() / "Lecturas"
PALABRA_CLAVE = "LEER"          # asunto del correo que dispara la vía 2


def entidades():
    try:
        from weave import ENTIDADES, PERSONAS
        return [(k, v[1]) for k, v in list(ENTIDADES.items()) + list(PERSONAS.items())]
    except Exception:
        return []


def indice():
    return json.loads(INDICE.read_text()) if INDICE.exists() else {}


def guardar_indice(d):
    INDICE.parent.mkdir(parents=True, exist_ok=True)
    INDICE.write_text(json.dumps(d, indent=1, ensure_ascii=False, sort_keys=True) + "\n")


def detectar(texto):
    """Entidades mencionadas, para enlazar la página destilada."""
    t = texto.lower()
    return [s for s, alias in entidades()
            if any(re.search(rf"(?<![\w\-]){re.escape(a.lower())}(?![\w\-])", t) for a in alias)]


def ingerir(titulo, cuerpo, origen, resumen="", ext=".md"):
    """Devuelve (slug, estado). Estado: 'nuevo' | 'duplicado'."""
    h = hashlib.sha256(cuerpo.encode("utf-8", "ignore") if isinstance(cuerpo, str)
                       else cuerpo).hexdigest()[:16]
    idx = indice()
    if h in idx:
        return idx[h]["slug"], "duplicado"

    hoy = datetime.date.today().isoformat()
    slug = slug_corto(titulo, entidades()) or "fuente"
    raw_slug = f"{hoy}-{slug}"
    destino = SOURCES / f"{raw_slug}{ext}"
    n = 2
    while destino.exists():
        destino = SOURCES / f"{raw_slug}-{n}{ext}"; n += 1
    SOURCES.mkdir(parents=True, exist_ok=True)

    if isinstance(cuerpo, bytes):
        destino.write_bytes(cuerpo)
    else:
        destino.write_text(
            f"---\ntitulo: {titulo}\norigen: {origen}\ncapturado: {hoy}\nsha: {h}\n"
            f"inmutable: true\n---\n\n{cuerpo}\n", encoding="utf-8")

    # Página destilada: viva, enlazada, reescribible.
    ents = detectar(f"{titulo} {cuerpo if isinstance(cuerpo, str) else ''}")
    d = DESTILADOS / f"{slug}.md"
    enlaces = "\n".join(f"- [[{e}]]" for e in ents[:8]) or "_Sin entidades detectadas todavía._"
    cuerpo_d = resumen.strip() or "_Pendiente de destilar._"
    d.write_text(
        f"---\ntitulo: {titulo}\nfuente: {destino.name}\ncapturado: {hoy}\n---\n\n"
        f"# {titulo}\n\n{cuerpo_d}\n\n## De dónde salió\n\n"
        f"- Origen: {origen}\n- Crudo intacto: `memory/sources/{destino.name}`\n\n"
        f"## Toca\n\n{enlaces}\n", encoding="utf-8")

    idx[h] = {"slug": slug, "raw": destino.name, "origen": origen, "fecha": hoy}
    guardar_indice(idx)
    return slug, "nuevo"


def cmd_add(a):
    if a.file:
        p = pathlib.Path(a.file).expanduser()
        if not p.exists():
            raise SystemExit(f"no existe: {p}")
        try:
            cuerpo, ext = p.read_text(errors="ignore"), ".md"
        except Exception:
            cuerpo, ext = p.read_bytes(), p.suffix
        titulo = a.titulo or p.stem
        origen = a.origen or f"archivo: {p.name}"
    else:
        cuerpo = pathlib.Path(a.texto).read_text(errors="ignore") if a.texto else (a.cuerpo or "")
        titulo, origen, ext = a.titulo or (a.url or "sin título"), a.url or a.origen or "sesión", ".md"
    slug, estado = ingerir(titulo, cuerpo, origen, a.resumen or "", ext)
    print(f"{estado}: {slug}")


def cmd_scan(a):
    """Vía 3: lo que haya en la carpeta vigilada entra y se retira de ahí."""
    if not VIGILADA.exists():
        VIGILADA.mkdir(parents=True, exist_ok=True)
        print(f"carpeta vigilada creada: {VIGILADA}")
        return
    procesados = VIGILADA / "_procesados"
    nuevos = 0
    for p in sorted(VIGILADA.iterdir()):
        if p.is_dir() or p.name.startswith("."):
            continue
        try:
            cuerpo, ext = p.read_text(errors="ignore"), ".md"
        except Exception:
            cuerpo, ext = p.read_bytes(), p.suffix
        slug, estado = ingerir(p.stem, cuerpo, f"carpeta vigilada: {p.name}", "", ext)
        procesados.mkdir(exist_ok=True)
        shutil.move(str(p), str(procesados / p.name))
        print(f"  {estado}: {slug}")
        nuevos += estado == "nuevo"
    print(f"carpeta vigilada: {nuevos} nuevos")


def cmd_list(a):
    for h, v in sorted(indice().items(), key=lambda kv: kv[1]["fecha"]):
        print(f"  {v['fecha']}  {v['slug']:38} {v['origen'][:50]}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add")
    a.add_argument("--file"); a.add_argument("--url"); a.add_argument("--texto")
    a.add_argument("--cuerpo"); a.add_argument("--titulo"); a.add_argument("--resumen")
    a.add_argument("--origen"); a.set_defaults(fn=cmd_add)
    sub.add_parser("scan").set_defaults(fn=cmd_scan)
    sub.add_parser("list").set_defaults(fn=cmd_list)
    args = ap.parse_args(); args.fn(args)


if __name__ == "__main__":
    main()
