#!/usr/bin/env python3
"""The weaver: backfill [[wikilinks]] across memory/, repeatably.

Design constraints, all of them load-bearing:

* **Idempotent.** Running it twice changes nothing. Inline links are only ever
  added to a BARE occurrence, so a second pass finds it already wrapped. The
  "Relacionado" block is delimited by markers and regenerated, never appended.
* **Never a bare first name.** "Marcelo" is a word; "Marcelo Treviño" is a
  person. Auto-linking first names turns every mention of a common word into a
  false edge, and the graph stops meaning anything.
* **Exclusions are honoured.** A card listed in memory/system/exclusiones-de-enlace.md
  or carrying `no_weave: true` is never touched, linked, or counted.
* **Capped.** A card gets at most MAX_INLINE inline links and MAX_RELATED in its
  block. Density belongs in hubs; a card that links to everything says nothing.
* Never leaves memory/. The private vaults are not its business.
"""
import argparse
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib import constants  # noqa: E402

MEM = constants.MEMORY_ROOT
MAX_INLINE = 6
MAX_RELATED = 8
INICIO, FIN = "<!-- weave:inicio -->", "<!-- weave:fin -->"

# slug de hub -> (título, [alias que lo disparan en el texto])
# Los alias deben ser inequívocos por sí solos. Nada de nombres de pila.
ENTIDADES = {
    "penske":          ("Penske", ["Penske"]),
    "element":         ("Element", ["Element Fleet", "Element"]),
    "bca":             ("BCA", ["BCA"]),
    "ford":            ("Ford", ["Ford"]),
    "zapata":          ("Zapata Logistics", ["Zapata"]),
    "kavak":           ("Kavak", ["Kavak"]),
    "centauro":        ("Piloto Centauro", ["Centauro"]),
    "turbofin":        ("Turbofin", ["Turbofin"]),
    "tesla":           ("Tesla", ["Tesla"]),
    "clicars":         ("Clicars", ["Clicars"]),
    "uber-av":         ("Uber AV", ["Uber AV", "Uber"]),
    "avasa":           ("Avasa", ["AVASA", "Avasa"]),
    "carta-responsiva":("Carta responsiva", ["carta responsiva", "Carta responsiva"]),
    "facturacion":     ("Facturación y cobranza", ["facturación", "cobranza", "Facturación"]),
    "cotizaciones":    ("Cotizaciones y tarifas", ["cotización", "cotizaciones", "tarifas"]),
}
# Personas: SOLO nombre completo. El nombre de pila solo nunca enlaza.
PERSONAS = {
    "fede-ranero": ("Fede Ranero", ["Fede Ranero"]),
    "nico-ariza": ("Nico Ariza", ["Nico Ariza", "Nicolás Ariza"]),
    "dan-rizzo": ("Dan Rizzo", ["Dan Rizzo"]),
    "jose-duran": ("José Durán", ["José Durán", "Jose Duran"]),
    "marcelo-trevino": ("Marcelo Treviño", ["Marcelo Treviño", "Marcelo Trevino"]),
    "uriel-vargas": ("Uriel Vargas", ["Uriel Vargas"]),
    "artur-morais": ("Artur Morais", ["Artur Morais"]),
    "paloma-calderon": ("Paloma Calderón", ["Paloma Calderón", "Paloma Calderon"]),
    "carolina-osses": ("Carolina Osses", ["Carolina Osses"]),
    "daniel-escribano": ("Daniel Escribano", ["Daniel Escribano"]),
    "juliana-turbofin": ("Juliana", ["Juliana Turbofin"]),
}


def frontmatter_no_weave(txt):
    m = re.match(r"^---\n(.*?)\n---", txt, re.S)
    return bool(m and re.search(r"^no_weave:\s*true", m.group(1), re.M))


def exclusiones():
    f = MEM / "system" / "exclusiones-de-enlace.md"
    out = {"exclusiones-de-enlace", "home", "glossary"}
    if f.exists():
        for line in f.read_text().splitlines():
            m = re.match(r"^-\s+([a-z0-9][a-z0-9\-]*)\s*$", line.strip())
            if m:
                out.add(m.group(1))
    return out


def cards():
    for d in sorted(p for p in MEM.iterdir() if p.is_dir() and not p.name.startswith(".")):
        for f in sorted(d.glob("*.md")):
            if f.name != "CLAUDE.md":
                yield f


def zonas_protegidas(txt):
    """Rangos que no se tocan: frontmatter, enlaces existentes, código, comentarios."""
    spans = []
    for pat in (r"^---\n.*?\n---", r"\[\[[^\]]*\]\]", r"`[^`]*`", r"<!--.*?-->",
                r"\[[^\]]*\]\([^)]*\)"):
        for m in re.finditer(pat, txt, re.S | re.M):
            spans.append(m.span())
    return spans


def dentro(pos, spans):
    return any(a <= pos < b for a, b in spans)


def enlazar_inline(txt, slug_actual, excl):
    """Envuelve la PRIMERA ocurrencia desnuda de cada alias. Tope: MAX_INLINE."""
    puestos = 0
    dicc = list(ENTIDADES.items()) + list(PERSONAS.items())
    for slug, (_titulo, alias) in dicc:
        if puestos >= MAX_INLINE or slug == slug_actual or slug in excl:
            continue
        if f"[[{slug}" in txt:           # ya enlazado en esta card
            continue
        for a in sorted(alias, key=len, reverse=True):
            spans = zonas_protegidas(txt)
            for m in re.finditer(rf"(?<![\w\-]){re.escape(a)}(?![\w\-])", txt):
                if dentro(m.start(), spans):
                    continue
                txt = txt[:m.start()] + f"[[{slug}|{a}]]" + txt[m.end():]
                puestos += 1
                break
            else:
                continue
            break
    return txt, puestos


def bloque_relacionado(slug, txt, hubs_de):
    destinos = [h for h in hubs_de.get(slug, []) if h != slug][:MAX_RELATED]
    if not destinos:
        return txt
    cuerpo = "\n".join(f"- [[{d}]]" for d in destinos)
    nuevo = f"{INICIO}\n## Relacionado\n\n{cuerpo}\n\n[[home|← Mapa]]\n{FIN}"
    if INICIO in txt:
        return re.sub(re.escape(INICIO) + r".*?" + re.escape(FIN), nuevo, txt, flags=re.S)
    return txt.rstrip() + "\n\n" + nuevo + "\n"


def alias_seguro(texto, limite=95):
    """Un título de card puede traer cualquier cosa: `[EXTERNAL]`, pipes, saltos.
    Dentro de [[slug|alias]] esos caracteres rompen el enlace — en Obsidian se
    ve roto, no solo en los verificadores. Se limpian antes de usarlos."""
    t = re.sub(r"[\[\]|]", " ", str(texto))
    return re.sub(r"\s+", " ", t).strip()[:limite]


def generar_hubs(excl):
    """Un hub por entidad/tema recurrente, con las cards que la mencionan.
    Regenerado entero en cada corrida: los hubs son derivados, no curados."""
    etiquetas = {"projects": "Qué está pasando", "context": "Contexto",
                 "rules": "Reglas que aplican", "people": "Gente"}
    for slug, (titulo, alias) in ENTIDADES.items():
        hits = []
        for f in cards():
            if f.stem in excl or f.stem == slug or f.parent.name == "topics":
                continue
            t = f.read_text(errors="ignore")
            if any(re.search(rf"(?<![\w\-]){re.escape(a)}(?![\w\-])", t) for a in alias):
                m = re.search(r"^titulo:\s*(.+)$", t, re.M)
                hits.append((f.stem, alias_seguro(m.group(1) if m else f.stem), f.parent.name))
        out = [f"---\ntitulo: {titulo}\nno_weave: true\n---\n", f"# {titulo}\n",
               "_Hub. Concentra la densidad de enlaces para que las cards sueltas "
               "se mantengan ligeras. Generado por `scripts/weave.py`._\n"]
        for folder, etiqueta in etiquetas.items():
            grupo = [h for h in hits if h[2] == folder]
            if grupo:
                out.append(f"## {etiqueta}\n")
                out += [f"- [[{sg}|{tt}]]" for sg, tt, _ in grupo]
                out.append("")
        if not hits:
            out.append("_Sin cards todavía._\n")
        out += ["---", "[[home|← Mapa]]"]
        (MEM / "topics" / f"{slug}.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    return len(ENTIDADES)


INDICES = {
    "indice-de-proyectos": ("projects", "Índice de proyectos",
        "Todo lo que el sistema sabe sobre frentes de trabajo, abiertos y cerrados."),
    "indice-de-reglas": ("rules", "Índice de reglas",
        "Todas las reglas que Armando ha dado. Se aplican solas; están aquí para discutirlas."),
    "indice-de-contexto": ("indice_contexto", "Índice de contexto",
        "Hechos durables que hay que tener presentes."),
}


def generar_indices(excl):
    """Un índice por carpeta, SIEMPRE completo.

    Los hubs de entidad dan significado, pero solo cubren lo que mencionan.
    Estos índices son la red de seguridad: garantizan que ninguna card quede
    inalcanzable, hoy y cuando la ingesta cree la número mil. Por eso se
    regeneran enteros en cada corrida en vez de curarse a mano.
    """
    import re as _re
    for slug, (folder, titulo, desc) in INDICES.items():
        real = "context" if folder == "indice_contexto" else folder
        d = MEM / real
        if not d.exists():
            continue
        filas = []
        for f in sorted(d.glob("*.md")):
            if f.name == "CLAUDE.md" or f.stem in excl:
                continue
            t = f.read_text(errors="ignore")
            m = _re.search(r"^titulo:\s*(.+)$", t, _re.M)
            filas.append(f"- [[{f.stem}|{alias_seguro(m.group(1) if m else f.stem)}]]")
        out = [f"---\ntitulo: {titulo}\nno_weave: true\n---\n", f"# {titulo}\n",
               f"_{desc} Generado por `scripts/weave.py`; no editar a mano._\n",
               f"**{len(filas)} cards**\n"] + filas + ["", "---", "[[home|← Mapa]]"]
        (MEM / "topics" / f"{slug}.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    return list(INDICES)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    excl = exclusiones()

    # Qué hubs tocan cada card, para su bloque Relacionado.
    hubs_de = {}
    for f in cards():
        if f.stem in excl:
            continue
        t = f.read_text(errors="ignore")
        tocan = [s for s, (_n, al) in ENTIDADES.items()
                 if any(re.search(rf"(?<![\w\-]){re.escape(a)}(?![\w\-])", t) for a in al)]
        hubs_de[f.stem] = tocan[:MAX_RELATED]

    cambiadas = inline_total = 0
    for f in cards():
        if f.stem in excl:
            continue
        orig = f.read_text(errors="ignore")
        if frontmatter_no_weave(orig):
            continue
        txt, n = enlazar_inline(orig, f.stem, excl)
        txt = bloque_relacionado(f.stem, txt, hubs_de)
        if txt != orig:
            cambiadas += 1
            inline_total += n
            if not args.dry_run:
                f.write_text(txt, encoding="utf-8")
    if not args.dry_run:
        nh = generar_hubs(excl)
        idx = generar_indices(excl)
        print(f"hubs regenerados: {nh}")
        print(f"índices regenerados: {', '.join(idx)}")
    print(f"cards modificadas: {cambiadas} · enlaces inline nuevos: {inline_total}"
          + ("  (simulacro)" if args.dry_run else ""))


if __name__ == "__main__":
    main()
