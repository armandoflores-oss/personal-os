"""Short, entity-first card names.

The filename IS the node label in Obsidian's graph. When a card is named after
the whole sentence it records, the graph fills with prose that reads like
instructions and you cannot see the clients, people and projects underneath.
A card's name should say WHAT it is about, entity first.
"""
import re

VACIAS = set("""a al algo ante antes como con contra cual cuando de del desde donde dos el
ella ellas ellos en entre era eran es esa ese eso esta este esto ha hace hacer hasta hay la
las le les lo los mas más me mi mucho muy no nos o para pero por porque que qué quien se sea
ser si sí sin sobre solo son su sus también tan te tiene todo tras un una uno unos y ya vez
está están fue fueron hacia cada otro otra otros otras""".split())
ESTADO = {"cerrada", "descartada", "cerrado", "descartado", "resuelta", "resuelto", "abierta"}
RELLENO = {"armando", "claude", "cuando", "corrige", "poner", "usar", "quedo", "tuvo", "hoy"}


def _norm(t):
    t = t.lower().strip()
    for a, b in (("á","a"),("é","e"),("í","i"),("ó","o"),("ú","u"),("ñ","n")):
        t = t.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def slug_corto(texto, entidades=(), max_palabras=4):
    """`entidades` es una lista de (slug, [alias]); la primera que aparezca manda."""
    s = _norm(texto)
    m = re.match(r"^([tpa]-\d+)-(.*)$", s)
    code, resto = (m.group(1), m.group(2)) if m else ("", s)
    prot = ""
    for slug, alias in entidades:
        if any(_norm(a) in resto for a in alias):
            prot = slug
            break
    pal = [w for w in resto.split("-") if w and w not in VACIAS
           and w not in ESTADO and w not in RELLENO]
    if prot:
        pal = [w for w in pal if w not in prot.split("-")]
    base = "-".join(([prot] if prot else []) + pal[:max_palabras - (1 if prot else 0)])
    return (f"{code}-{base}" if code else base) or (code or "sin-titulo")
