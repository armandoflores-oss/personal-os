#!/usr/bin/env python3
"""The nightly loop: prepare, judge, apply, grade.

Only ONE of the four stages is a model. The other three are code, and that is
the whole point: a model that both gathers the evidence and decides on it can
talk itself into anything. Here it only gets to label evidence it did not
choose, and the labels it produces run into guardrails it cannot argue with.

  loop.py prepare                     -> candidatos del día (determinista)
  loop.py apply --decisiones <f>      -> aplica con guardarraíles (determinista)
  loop.py grade [--fecha YYYY-MM-DD]  -> califica el día (determinista)
"""
import argparse
import collections
import datetime
import hashlib
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib import constants, gate  # noqa: E402
from lib.events import append_event, read_events  # noqa: E402
from lib.feedback import read_feedback  # noqa: E402
from lib.replay import replay  # noqa: E402

LOOP = constants.REPO_ROOT / "state" / "loop"
EVALS = constants.REPO_ROOT / "state" / "evals"
CACHE = constants.REPO_ROOT / "cache"
SYNCS = constants.REPO_ROOT / "syncs"

# Tope de mutaciones por noche. Elegido con los números reales de Armando, no
# por costumbre: el sistema cierra ~0.5 tareas/noche por evidencia y tiene ~14
# abiertas. 6 es cuatro veces una noche normal —así que nunca estorba— y menos
# de la mitad del tablero, así que una noche descompuesta es un fastidio
# reversible y no un borrón. El spec sugería ~15; con este tamaño de tablero
# eso no sería un tope, sería permiso para vaciarlo.
MAX_MUTACIONES = 6
VENTANA_PROPUESTA_H = 72


def hoy():
    return datetime.date.today().isoformat()


def abiertas():
    return [t for t in replay().values() if t["status"] == "open" and not t["archived"]]


def tokens(texto):
    return {w for w in gate.norm(texto).split() if len(w) > 4}


# ---------------------------------------------------------------- PREPARE
def cmd_prepare(args):
    """Junta evidencia para cada item abierto. Sin juicio, sin modelo."""
    eventos = read_events()
    por_tarea = collections.defaultdict(list)
    for e in eventos:
        por_tarea[e["task_id"]].append(e)

    dicho = [(f.get("text") or "") + " " + (f.get("lesson") or "")
             for f in read_feedback() if not f.get("firewalled")]
    transcripciones = []
    d = CACHE / "transcripts"
    if d.exists():
        for f in d.glob("*.txt"):
            try:
                edad = datetime.datetime.now() - datetime.datetime.fromtimestamp(f.stat().st_mtime)
            except OSError:
                continue
            if edad.days <= 3:
                transcripciones.append(gate.norm(f.read_text(errors="ignore")))

    candidatos = []
    ahora = datetime.datetime.now(datetime.timezone.utc)
    for t in abiertas():
        tk = tokens(t["title"])
        ev = []
        if len(tk) >= 3:
            need = max(2, round(len(tk) * 0.5))
            for frase in dicho:
                n = len([x for x in tk if x in gate.norm(frase)])
                if n >= need:
                    ev.append({"tipo": "armando_lo_dijo", "detalle": frase[:180], "tokens": n})
                    break
            for tr in transcripciones:
                n = len([x for x in tk if x in tr])
                if n >= need:
                    ev.append({"tipo": "se_trato_en_junta", "tokens": n})
                    break
        ultimos = sorted(por_tarea.get(t["task_id"], []), key=lambda e: e["ts"])
        if ultimos:
            try:
                dias = (ahora - datetime.datetime.fromisoformat(ultimos[-1]["ts"])).days
            except ValueError:
                dias = 0
            if dias >= 14:
                ev.append({"tipo": "sin_movimiento", "dias": dias})
        if ev:
            candidatos.append({"task_id": t["task_id"], "code": t["code"],
                               "titulo": t["title"][:120], "dominio": t["domain"],
                               "evidencia": ev})

    LOOP.mkdir(parents=True, exist_ok=True)
    f = LOOP / f"candidatos-{hoy()}.json"
    f.write_text(json.dumps({"fecha": hoy(), "abiertas": len(abiertas()),
                             "candidatos": candidatos}, ensure_ascii=False, indent=1))
    print(json.dumps({"archivo": str(f), "abiertas": len(abiertas()),
                      "candidatos": len(candidatos)}, ensure_ascii=False))


# ------------------------------------------------------------------ APPLY
def cargar_propuestas():
    f = LOOP / "propuestas.json"
    return json.loads(f.read_text()) if f.exists() else {}


def guardar_propuestas(d):
    (LOOP / "propuestas.json").write_text(json.dumps(d, indent=1, ensure_ascii=False, sort_keys=True) + "\n")


def cmd_apply(args):
    # Vetos y vencimientos primero: si Armando tocó algo, esa propuesta muere
    # antes de que se evalúe nada nuevo sobre ella.
    cmd_ledger(argparse.Namespace())
    ruta = pathlib.Path(args.decisiones)
    crudo = ruta.read_text()
    sello = hashlib.sha256(crudo.encode()).hexdigest()[:16]
    aplicados = json.loads((LOOP / "aplicados.json").read_text()) if (LOOP / "aplicados.json").exists() else {}
    if sello in aplicados:
        print(json.dumps({"estado": "ya_aplicado", "sello": sello,
                          "cuando": aplicados[sello]}, ensure_ascii=False))
        return

    decisiones = json.loads(crudo).get("decisiones", [])
    estado = {t["task_id"]: t for t in replay().values()}
    props = cargar_propuestas()
    cerradas, propuestas, rechazadas = [], [], []
    mutaciones = 0

    for d in decisiones:
        tid, clase = d.get("task_id"), d.get("clase")
        t = estado.get(tid)
        # 1. el id tiene que existir y seguir abierto, contra el estado REAL
        if not t:
            rechazadas.append({"task_id": tid, "por": "id inexistente"}); continue
        if t["status"] != "open" or t["archived"]:
            rechazadas.append({"code": t["code"], "por": "ya no está abierta"}); continue
        if clase not in ("dura", "blanda"):
            rechazadas.append({"code": t["code"], "por": f"clase {clase!r} no acciona"}); continue
        # 2. firewalled nunca se cierra solo: se degrada a propuesta, siempre
        if t["domain"] in constants.FIREWALLED_DOMAINS and clase == "dura":
            clase = "blanda"
            d["degradada"] = "dominio firewalled"
        # 3. tope de mutaciones
        if clase == "dura" and mutaciones >= MAX_MUTACIONES:
            rechazadas.append({"code": t["code"], "por": f"tope de {MAX_MUTACIONES} alcanzado"})
            continue

        if clase == "dura":
            append_event({"kind": "set_status", "actor": "system:loop", "task_id": tid,
                          "payload": {"status": "done",
                                      "evidence": (d.get("evidencia") or "cerrada por el loop")[:300]}})
            mutaciones += 1
            cerradas.append({"code": t["code"], "titulo": t["title"][:80],
                             "evidencia": (d.get("evidencia") or "")[:200]})
        else:
            vence = (datetime.datetime.now(datetime.timezone.utc)
                     + datetime.timedelta(hours=VENTANA_PROPUESTA_H)).isoformat(timespec="seconds")
            if tid in props and props[tid].get("vetada"):
                rechazadas.append({"code": t["code"], "por": "vetada para siempre"}); continue
            props[tid] = {"code": t["code"], "titulo": t["title"][:120],
                          "creada": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
                          "evidencia": (d.get("evidencia") or "")[:200],
                          "vence": vence, "degradada": d.get("degradada"),
                          "firewalled": t["domain"] in constants.FIREWALLED_DOMAINS}
            propuestas.append({"code": t["code"], "vence": vence})

    guardar_propuestas(props)
    aplicados[sello] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    (LOOP / "aplicados.json").write_text(json.dumps(aplicados, indent=1, sort_keys=True) + "\n")
    # 'ts' y no solo 'fecha': el brief filtra los recibos por antigüedad con ese
    # campo, y sin él descarta en silencio todo lo que el loop hizo.
    recibo = {"ts": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
              "fecha": hoy(), "leg": "loop", "cerradas": cerradas,
              "propuestas": propuestas, "rechazadas": rechazadas,
              "tope": MAX_MUTACIONES, "sello": sello}
    SYNCS.mkdir(exist_ok=True)
    with open(SYNCS / f"{hoy()}.ndjson", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(recibo, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps(recibo, ensure_ascii=False, indent=1))


# ------------------------------------------------------------------ GRADE
def cmd_grade(args):
    fecha = args.fecha or (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    ev = read_events()
    dia = [e for e in ev if e["ts"][:10] == fecha]

    cerradas_sistema = {e["task_id"] for e in dia
                        if e["actor"].startswith("system:") and e["kind"] == "set_status"
                        and (e.get("payload") or {}).get("status") == "done"}
    # resucitadas: el sistema la cerró y DESPUÉS alguien la reabrió
    resucitadas = 0
    for tid in cerradas_sistema:
        post = [e for e in ev if e["task_id"] == tid and e["ts"][:10] >= fecha
                and (e.get("payload") or {}).get("status") == "open"]
        resucitadas += bool(post)
    # intervenciones de Armando: sus eventos, no los del sistema
    intervenciones = len([e for e in dia if e["actor"] == "user"])
    duplicados = 0
    sup = constants.REPO_ROOT / "state" / "suppressed.ndjson"
    if sup.exists():
        for l in sup.read_text().splitlines():
            if l.strip():
                r = json.loads(l)
                if r.get("ts", "")[:10] == fecha and r.get("reason") == "duplicado":
                    duplicados += 1
    sin_recibo = 0
    f = SYNCS / f"{fecha}.ndjson"
    if cerradas_sistema and not f.exists():
        sin_recibo = len(cerradas_sistema)

    score = 10 - 3*resucitadas - 1*min(duplicados, 3) - 1*min(intervenciones, 3) - 1*sin_recibo
    score = max(0, min(10, score))
    linea = {"fecha": fecha, "score": score, "resucitadas": resucitadas,
             "duplicados": duplicados, "intervenciones_usuario": intervenciones,
             "cierres_sistema": len(cerradas_sistema), "sin_recibo": sin_recibo,
             "abiertas_al_calificar": len(abiertas())}
    EVALS.mkdir(parents=True, exist_ok=True)
    f = EVALS / "trend.ndjson"
    lineas = [l for l in (f.read_text().splitlines() if f.exists() else [])
              if l.strip() and json.loads(l)["fecha"] != fecha]     # idempotente
    lineas.append(json.dumps(linea, ensure_ascii=False, sort_keys=True))
    f.write_text("\n".join(sorted(lineas, key=lambda l: json.loads(l)["fecha"])) + "\n")
    print(json.dumps(linea, ensure_ascii=False))


# ----------------------------------------------------------------- LEDGER
def cmd_ledger(args):
    """Vetos y vencimientos. Corre antes del brief y dentro del loop.

    Tres reglas, y las tres son del spec por una razón:
    * Cualquier acción de Armando sobre el item ES un veto. No hay que
      preguntarle; que se haya metido ya dice todo lo que hacía falta saber.
    * El veto es permanente. La entrada se queda vetada para siempre, así que
      eso no se le vuelve a proponer aunque la evidencia reaparezca.
    * Lo firewalled NUNCA vence. Espera indefinidamente a que él lo toque.
    """
    props = cargar_propuestas()
    if not props:
        print(json.dumps({"propuestas": 0}, ensure_ascii=False)); return
    eventos = read_events()
    estado = replay()
    ahora = datetime.datetime.now(datetime.timezone.utc)
    vetadas, vencidas, esperando = [], [], []

    for tid, p in props.items():
        if p.get("vetada"):
            continue
        # ¿Armando tocó el item después de que se propuso? Eso es el veto.
        suyos = [e for e in eventos if e["task_id"] == tid and e["actor"] == "user"
                 and e["ts"] > p.get("creada", "")]
        if suyos:
            p["vetada"] = True
            p["vetada_el"] = ahora.isoformat(timespec="seconds")
            p["motivo"] = f"Armando actuó sobre el item ({suyos[-1]['kind']})"
            vetadas.append({"code": p["code"], "motivo": p["motivo"]})
            continue
        if p.get("firewalled"):
            esperando.append({"code": p["code"], "por": "firewalled: no vence nunca"})
            continue
        if p.get("vence") and ahora.isoformat(timespec="seconds") >= p["vence"]:
            t = estado.get(tid)
            if not t or t["status"] != "open" or t["archived"]:
                p["vetada"] = True
                p["motivo"] = "el item ya no estaba abierto al vencer"
                continue
            append_event({"kind": "set_status", "actor": "system:loop:propuesta",
                          "task_id": tid,
                          "payload": {"status": "done",
                                      "evidence": f"propuesta vencida sin objeción · {p.get('evidencia','')[:200]}"}})
            p["aplicada"] = ahora.isoformat(timespec="seconds")
            p["vetada"] = True          # cerrada: no se vuelve a proponer
            vencidas.append({"code": p["code"], "titulo": p.get("titulo", "")[:80],
                             "evidencia": p.get("evidencia", "")[:200]})
        else:
            esperando.append({"code": p["code"], "vence": p.get("vence")})

    guardar_propuestas(props)
    recibo = {"ts": ahora.isoformat(timespec="seconds"), "fecha": hoy(), "leg": "propuestas",
              "vetadas": vetadas, "vencidas": vencidas, "esperando": len(esperando)}
    if vetadas or vencidas:
        SYNCS.mkdir(exist_ok=True)
        with open(SYNCS / f"{hoy()}.ndjson", "a", encoding="utf-8") as fh:
            fh.write(json.dumps(recibo, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps(recibo, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("prepare").set_defaults(fn=cmd_prepare)
    sub.add_parser("ledger").set_defaults(fn=cmd_ledger)
    a = sub.add_parser("apply"); a.add_argument("--decisiones", required=True); a.set_defaults(fn=cmd_apply)
    g = sub.add_parser("grade"); g.add_argument("--fecha"); g.set_defaults(fn=cmd_grade)
    args = ap.parse_args(); args.fn(args)


if __name__ == "__main__":
    main()
