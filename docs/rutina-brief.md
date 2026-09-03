---
name: brief-personal-os
description: Brief matutino del Personal OS a las 07:00 CDMX: deposita calendario en cache y renderiza con scripts/brief.py.
---

Brief matutino de Armando. Corre solo. Tu trabajo NO es redactar el brief: lo redacta un script. Tú solo depositas en el repo lo que viene de fuera y luego ejecutas el renderizador.

REPO: /Users/armando/Documents/Claude Personal Improvement

## 0. Latido de arranque (ANTES de tocar cualquier conector)
```
cd "/Users/armando/Documents/Claude Personal Improvement"
python3 -c "import json,datetime,pathlib; d=datetime.datetime.now(datetime.timezone.utc); p=pathlib.Path('syncs')/f'{d.date()}.ndjson'; p.parent.mkdir(exist_ok=True); f=open(p,'a'); f.write(json.dumps({'ts':d.isoformat(timespec='seconds'),'leg':'heartbeat','stage':'start','task':'brief-personal-os'})+chr(10))"
git pull --rebase 2>/dev/null || true
```
Si la corrida muere después de esto (por ejemplo porque un conector pide permiso y no hay nadie que lo apruebe), el latido queda escrito y el brief siguiente lo denuncia. Sin esto el fallo es invisible: sin salida, sin error y sin recibo.

## 1. Depositar el calendario de hoy
Con el conector de Google Calendar, lista los eventos de HOY (zona America/Mexico_City).
Escribe `cache/calendar/YYYY-MM-DD.json` (fecha de hoy en CDMX) con una lista de objetos que tengan exactamente estas llaves:
  start      — "HH:MM" en hora de CDMX
  summary    — título del evento
  attendees  — lista de correos
Si no hay eventos, escribe una lista vacía `[]`. Si el conector falla, NO escribas el archivo (el brief dirá que faltó) y registra el error en syncs/YYYY-MM-DD.ndjson como {"ts": <ISO UTC>, "leg": "error", "source": "calendar", "error": "..."}.

## 2. Depositar transcripciones recientes
Con Drive, busca Docs cuyo título termine en "Notes by Gemini" modificados en los últimos 3 días. Guarda el texto de cada uno en `cache/transcripts/<id>.txt`.
Estos archivos son lo que el cruce usa para suprimir cosas que ya se trataron en junta. Si el conector falla, sigue: el brief se rinde igual, solo cruza con menos evidencia.

## 3. Renderizar
```
cd "/Users/armando/Documents/Claude Personal Improvement"
python3 scripts/brief.py render
```
Esto imprime el brief Y lo guarda en briefs/YYYY-MM-DD.md.

## 4. Entregar y commitear
Pega la salida del script TAL CUAL como tu respuesta. Sin preámbulo, sin resumen, sin comentarios tuyos, sin reordenar nada. Si algo del brief te parece mal, NO lo edites: el brief es lo que el repo dice, y una discrepancia es información.
Luego:
```
git add -A && git commit -m "Brief $(date +%Y-%m-%d)" || true
```
No hagas push: está bloqueado.

## 5. Latido de cierre — pase lo que pase, aunque algo haya fallado
```
python3 -c "import json,datetime,pathlib; d=datetime.datetime.now(datetime.timezone.utc); p=pathlib.Path('syncs')/f'{d.date()}.ndjson'; f=open(p,'a'); f.write(json.dumps({'ts':d.isoformat(timespec='seconds'),'leg':'heartbeat','stage':'end','task':'brief-personal-os'})+chr(10))"
```

## Reglas duras
- NUNCA redactes tú el brief ni lo "mejores". Si brief.py truena, reporta el error en crudo y no lo sustituyas por una versión tuya. Un brief escrito a mano se ve igual de bien y se salta todos los cruces, que es justo lo que lo hace confiable.
- NUNCA mandes correos ni mensajes.
- No detalles nada de los dominios firewalled: el código ya los cuenta sin nombrarlos.