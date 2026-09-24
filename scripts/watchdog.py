#!/usr/bin/env python3
"""El watchdog. Verifica cada etapa obligatoria y NUNCA rompe nada.

Cuatro decisiones que lo definen, todas del spec y todas por una razón:

* **Siempre sale con código 0.** Un watchdog que tumba la tubería que vigila es
  peor que no tener watchdog: la primera vez que falla, alguien lo apaga.
* **Un componente que truena reporta ÁMBAR con su error.** Nunca desaparece en
  silencio. Un check roto que no se ve equivale a un check que dice "verde".
* **La frescura sale de fechas DENTRO del contenido**, nunca de la fecha de
  modificación del archivo. Un `touch`, un `git checkout` o un respaldo mueven
  el mtime sin que nada haya corrido.
* **Sabe de fines de semana.** Las rutinas corren de lunes a viernes; alarmar un
  domingo enseña a ignorar la alarma.

  watchdog.py check          -> tabla legible
  watchdog.py check --json   -> para el brief
"""
import argparse
import datetime
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib import constants  # noqa: E402

MANIFIESTO = constants.REPO_ROOT / "config" / "manifiesto.json"
SYNCS = constants.REPO_ROOT / "syncs"
VERDE, AMBAR, PARKED = "verde", "ambar", "parked"


def ahora():
    return datetime.datetime.now(datetime.timezone.utc)


def habiles_desde(desde, hasta):
    """Días hábiles entre dos fechas. Un lunes no debe exigir que algo haya
    corrido el sábado."""
    d, n = desde.date(), 0
    while d < hasta.date():
        d += datetime.timedelta(days=1)
        if d.weekday() < 5:
            n += 1
    return n


def _recibos(dias=6):
    """Todos los recibos recientes, leídos por su ts INTERNO."""
    out = []
    for i in range(dias):
        f = SYNCS / f"{(ahora().date() - datetime.timedelta(days=i)).isoformat()}.ndjson"
        if not f.exists():
            continue
        for l in f.read_text(errors="ignore").splitlines():
            if not l.strip():
                continue
            try:
                r = json.loads(l)
                if "ts" in r:
                    out.append(r)
            except json.JSONDecodeError:
                continue
    return out


def _edad_horas(ts):
    try:
        t = datetime.datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        if t.tzinfo is None:
            t = t.replace(tzinfo=datetime.timezone.utc)
        return (ahora() - t).total_seconds() / 3600
    except (ValueError, TypeError):
        return None


# ------------------------------------------------------- checks por tipo
def chk_recibo(et, ctx):
    asercion = et["asercion"]
    cands = []
    for r in ctx["recibos"]:
        if asercion.startswith("heartbeat/"):
            _, etapa, tarea = asercion.split("/")
            if r.get("leg") == "heartbeat" and r.get("stage") == etapa and r.get("task") == tarea:
                cands.append(r["ts"])
        elif r.get("leg") == asercion:
            cands.append(r["ts"])
    if not cands:
        return AMBAR, f"sin la línea `{asercion}` en los últimos días"
    h = _edad_horas(max(cands))
    if h is None:
        return AMBAR, "la línea existe pero su fecha es ilegible"
    return (VERDE, f"hace {h:.0f}h") if h <= et["horas"] else (AMBAR, f"hace {h:.0f}h (tope {et['horas']}h)")


def chk_watermark(et, ctx):
    f = constants.REPO_ROOT / "state" / "watermarks.json"
    if not f.exists():
        return AMBAR, "no hay archivo de marcas de agua"
    w = json.loads(f.read_text())
    if et["clave"] not in w:
        return AMBAR, f"sin marca para {et['clave']}"
    h = _edad_horas(w[et["clave"]])
    if h is None:
        return AMBAR, f"marca ilegible: {w[et['clave']]!r}"
    if h < 0:
        return AMBAR, f"la marca está en el futuro ({w[et['clave']]})"
    return (VERDE, f"hace {h:.0f}h") if h <= et["horas"] else (AMBAR, f"hace {h:.0f}h (tope {et['horas']}h)")


def chk_brief_del_dia(et, ctx):
    """La fecha sale del ENCABEZADO del brief, no del nombre ni del mtime."""
    d = constants.REPO_ROOT / "briefs"
    if not d.exists():
        return AMBAR, "no hay carpeta de briefs"
    fechas = []
    for f in d.glob("*.md"):
        m = re.search(r"^# Brief · \w+ (\d{1,2}) de (\w+) de (\d{4})", f.read_text(errors="ignore"), re.M)
        if m:
            meses = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto",
                     "septiembre","octubre","noviembre","diciembre"]
            try:
                fechas.append(datetime.date(int(m.group(3)), meses.index(m.group(2)) + 1, int(m.group(1))))
            except ValueError:
                continue
    if not fechas:
        return AMBAR, "ningún brief declara su fecha en el encabezado"
    ultimo = max(fechas)
    n = habiles_desde(datetime.datetime.combine(ultimo, datetime.time(), datetime.timezone.utc), ahora())
    return (VERDE, f"último: {ultimo}") if n <= 1 else (AMBAR, f"el último es de {ultimo}, hace {n} días hábiles")


def chk_trend(et, ctx):
    f = constants.REPO_ROOT / "state" / "evals" / "trend.ndjson"
    if not f.exists():
        return AMBAR, "no hay archivo de tendencia"
    fechas = [json.loads(l)["fecha"] for l in f.read_text().splitlines() if l.strip()]
    if not fechas:
        return AMBAR, "tendencia vacía"
    ultimo = max(fechas)
    n = habiles_desde(datetime.datetime.fromisoformat(ultimo + "T00:00:00+00:00"), ahora())
    return (VERDE, f"última: {ultimo}") if n <= 2 else (AMBAR, f"la última es de {ultimo}, hace {n} días hábiles")


def chk_tejido_huerfanas(et, ctx):
    tej = [r for r in ctx["recibos"] if r.get("leg") == "tejido"]
    if not tej:
        return AMBAR, "el tejedor no ha dejado línea"
    ult = max(tej, key=lambda r: r["ts"])
    h = ult.get("huerfanas", -1)
    if h < 0:
        return AMBAR, "el tejedor no pudo medir la cobertura"
    return (VERDE, f"{ult.get('cards','?')} cards, 0 huérfanas") if h == 0 else (AMBAR, f"{h} cards inalcanzables")


def chk_changelog(et, ctx):
    f = constants.MEMORY_ROOT / "changelog.md"
    if not f.exists():
        return AMBAR, "no hay changelog"
    fechas = re.findall(r"^## (\d{4}-\d{2}-\d{2})", f.read_text(errors="ignore"), re.M)
    if not fechas:
        return AMBAR, "el changelog no tiene entradas fechadas"
    ultimo = max(fechas)
    n = habiles_desde(datetime.datetime.fromisoformat(ultimo + "T00:00:00+00:00"), ahora())
    return (VERDE, f"última: {ultimo}") if n <= 1 else (AMBAR, f"la última es de {ultimo}, hace {n} días hábiles")


def chk_credenciales(et, ctx):
    creds = [c for c in ctx["man"].get("credenciales", []) if c.get("vence")]
    if not creds:
        return VERDE, "ninguna credencial con vencimiento declarado"
    avisos = []
    for c in creds:
        try:
            dias = (datetime.date.fromisoformat(c["vence"]) - ahora().date()).days
        except ValueError:
            avisos.append(f"{c.get('nombre','?')}: fecha ilegible"); continue
        if dias <= et.get("avisar_dias", 30):
            avisos.append(f"{c.get('nombre','?')}: {dias} días")
    return (AMBAR, " · ".join(avisos)) if avisos else (VERDE, f"{len(creds)} credencial(es), ninguna próxima")


def chk_parked(et, ctx):
    rev = et.get("revisar")
    if rev:
        try:
            if datetime.date.fromisoformat(rev) <= ahora().date():
                return AMBAR, f"aparcada desde {et.get('desde')} y ya venció su revisión ({rev}): {et.get('razon')}"
        except ValueError:
            return AMBAR, f"fecha de revisión ilegible: {rev!r}"
    return PARKED, f"{et.get('razon')} · revisar {rev or 'sin fecha'}"


CHECKS = {"recibo": chk_recibo, "watermark": chk_watermark, "brief_del_dia": chk_brief_del_dia,
          "trend": chk_trend, "tejido_huerfanas": chk_tejido_huerfanas, "changelog": chk_changelog,
          "credenciales": chk_credenciales, "parked": chk_parked}



def _parqueo(ap, et, ctx):
    """Devuelve (estado, detalle) si el parqueo manda, o (None, None) si venció.

    Un parqueo sin fecha de revisión es olvidar algo con estilo, así que la
    fecha es obligatoria: sin ella, el parqueo no vale y la etapa se revisa
    normal. Cuando la fecha llega, el parqueo NO se renueva solo — la etapa
    vuelve a alarmar para que Armando decida otra vez.
    """
    rev = ap.get("revisar")
    if not rev:
        return AMBAR, f"aparcada sin fecha de revisión: {ap.get('razon','sin razón')}"
    try:
        vence = datetime.date.fromisoformat(rev)
    except ValueError:
        return AMBAR, f"fecha de revisión ilegible: {rev!r}"
    if vence > ahora().date():
        dias = (vence - ahora().date()).days
        return PARKED, f"{ap.get('razon','sin razón')} · desde {ap.get('desde','?')} · revisar en {dias} días"
    return None, None      # venció: que corra el check real y que se note


def evaluar():
    try:
        man = json.loads(MANIFIESTO.read_text())
    except Exception as e:
        return {"estado": AMBAR, "etapas": [{"id": "manifiesto", "estado": AMBAR,
                "detalle": f"no pude leer el manifiesto: {e}"}]}
    ctx = {"man": man, "recibos": _recibos()}
    fin_de_semana = ahora().weekday() >= 5
    filas = []
    for prod in man.get("productores", []):
        solo_habiles = prod.get("dias") == "L-V"
        for et in prod.get("etapas", []):
            if solo_habiles and fin_de_semana and et.get("tipo") != "parked":
                filas.append({"id": et["id"], "productor": prod["nombre"], "nombre": et["nombre"],
                              "estado": VERDE, "detalle": "fin de semana: no se exige"})
                continue
            ap = et.get("aparcada")
            if ap:
                estado, detalle = _parqueo(ap, et, ctx)
                if estado is not None:
                    filas.append({"id": et["id"], "productor": prod["nombre"],
                                  "nombre": et["nombre"], "estado": estado, "detalle": detalle})
                    continue
            fn = CHECKS.get(et.get("tipo"))
            if fn is None:
                filas.append({"id": et["id"], "productor": prod["nombre"], "nombre": et["nombre"],
                              "estado": AMBAR, "detalle": f"tipo de check desconocido: {et.get('tipo')!r}"})
                continue
            try:
                estado, detalle = fn(et, ctx)
            except Exception as e:      # un check roto NUNCA desaparece
                estado, detalle = AMBAR, f"el check tronó: {type(e).__name__}: {e}"
            if ap:
                # El parqueo venció. Aunque el check pase, hay que decidir de
                # nuevo: extenderlo, quitarlo, o aceptar que el componente vive.
                estado = AMBAR
                detalle = (f"venció su parqueo ({ap.get('revisar')}) · "
                           f"era: {ap.get('razon','')} · ahora: {detalle} · "
                           f"decide: apárcala de nuevo o quítale el parqueo")
            filas.append({"id": et["id"], "productor": prod["nombre"], "nombre": et["nombre"],
                          "estado": estado, "detalle": detalle})
    global_ = AMBAR if any(f["estado"] == AMBAR for f in filas) else VERDE
    return {"estado": global_, "fin_de_semana": fin_de_semana, "etapas": filas}



def cmd_park(a):
    man = json.loads(MANIFIESTO.read_text())
    for prod in man["productores"]:
        for et in prod["etapas"]:
            if et["id"] == a.etapa:
                if a.quitar:
                    et.pop("aparcada", None)
                    msg = f"{a.etapa}: parqueo retirado, vuelve a vigilarse normal"
                else:
                    et["aparcada"] = {"razon": a.razon or "sin razón dada",
                                      "desde": datetime.date.today().isoformat(),
                                      "revisar": a.revisar}
                    msg = f"{a.etapa}: aparcada hasta {a.revisar} · {a.razon}"
                MANIFIESTO.write_text(json.dumps(man, indent=1, ensure_ascii=False) + "\n")
                print(msg)
                return
    print(f"no existe la etapa {a.etapa!r}. Las que hay:", file=sys.stderr)
    for prod in man["productores"]:
        for et in prod["etapas"]:
            print(f"  {et['id']}", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd")
    c = sub.add_parser("check"); c.add_argument("--json", action="store_true")
    pk = sub.add_parser("park")
    pk.add_argument("etapa"); pk.add_argument("--razon"); pk.add_argument("--revisar")
    pk.add_argument("--quitar", action="store_true")
    a = ap.parse_args(["check"] if len(sys.argv) == 1 else None)
    if a.cmd == "park":
        if not a.quitar and not a.revisar:
            print("falta --revisar: un parqueo sin fecha es olvidar con estilo", file=sys.stderr)
            sys.exit(0)
        cmd_park(a); sys.exit(0)
    a.json = getattr(a, "json", False)
    try:
        r = evaluar()
    except Exception as e:
        r = {"estado": AMBAR, "etapas": [{"id": "watchdog", "estado": AMBAR,
             "detalle": f"el watchdog mismo tronó: {type(e).__name__}: {e}"}]}
    if a.json:
        print(json.dumps(r, ensure_ascii=False))
    else:
        icono = {VERDE: "verde ", AMBAR: "ÁMBAR ", PARKED: "aparcada"}
        print(f"=== watchdog: {r['estado'].upper()} ===")
        for f in r["etapas"]:
            print(f"  {icono.get(f['estado'],'?'):9} {f['id']:26} {f['detalle'][:70]}")
    sys.exit(0)        # SIEMPRE 0. Un watchdog no tumba lo que vigila.


if __name__ == "__main__":
    main()
