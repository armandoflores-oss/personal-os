---
name: brief-personal-os
description: Brief matutino del Personal OS a las 07:00 CDMX: deposita calendario en cache y renderiza con scripts/brief.py.
---

Brief matutino de Armando. Corre solo. Tu trabajo NO es redactar el brief: lo redacta un script. Tú depositas en el repo lo que viene de fuera, ejecutas el renderizador, y le entregas la salida por Slack.

REPO: /Users/armando/Documents/Claude Personal Improvement

## 0. Latido de arranque (ANTES de tocar cualquier conector)
```
cd "/Users/armando/Documents/Claude Personal Improvement"
python3 -c "import json,datetime,pathlib; d=datetime.datetime.now(datetime.timezone.utc); p=pathlib.Path('syncs')/f'{d.date()}.ndjson'; p.parent.mkdir(exist_ok=True); f=open(p,'a'); f.write(json.dumps({'ts':d.isoformat(timespec='seconds'),'leg':'heartbeat','stage':'start','task':'brief-personal-os'})+chr(10))"
git pull --rebase 2>/dev/null || true
```

## 1. Depositar el calendario de hoy
Con el conector de Google Calendar, lista los eventos de HOY (zona America/Mexico_City).
Escribe `cache/calendar/YYYY-MM-DD.json` (fecha de hoy en CDMX) con una lista de objetos con exactamente estas llaves:
  start "HH:MM" en hora de CDMX · summary título · attendees lista de correos
Si no hay eventos escribe `[]`. Si el conector falla NO escribas el archivo y registra el error en syncs/YYYY-MM-DD.ndjson como {"ts": <ISO UTC>, "leg": "error", "source": "calendar", "error": "..."}.

## 2. Depositar transcripciones recientes
Con Drive, busca Docs cuyo título termine en "Notes by Gemini" modificados en los últimos 3 días. Guarda el texto de cada uno en `cache/transcripts/<id>.txt`. Son lo que el cruce usa para suprimir lo ya tratado en junta. Si falla, sigue.

## 3. Renderizar
```
cd "/Users/armando/Documents/Claude Personal Improvement"
python3 scripts/brief.py render
```
Imprime el brief y lo guarda en briefs/YYYY-MM-DD.md.

## 4. ENTREGAR por Slack — este es el paso que importa
Manda la salida COMPLETA del script como DM a Armando con slack_send_message:
  channel_id: U077GQC532M
  message: la salida literal de brief.py, tal cual, sin recortar ni reordenar
Si pasa de 5000 caracteres, pártelo en dos mensajes cortando entre secciones (nunca a media sección) y manda el segundo inmediatamente después.
Este es el ÚNICO mensaje que tienes permitido mandar, y U077GQC532M el único destinatario. No mandes nada a ningún canal ni a ninguna otra persona, pase lo que pase.
Si el envío falla, registra {"ts":..., "leg":"error", "source":"slack", "error":...} en syncs/ y continúa: el brief ya quedó en briefs/.

## 5. Commit
```
git add -A && git commit -m "Brief $(date +%Y-%m-%d)" || true
```
No hagas push: está bloqueado.

## 6. Latido de cierre — pase lo que pase
```
python3 -c "import json,datetime,pathlib; d=datetime.datetime.now(datetime.timezone.utc); p=pathlib.Path('syncs')/f'{d.date()}.ndjson'; f=open(p,'a'); f.write(json.dumps({'ts':d.isoformat(timespec='seconds'),'leg':'heartbeat','stage':'end','task':'brief-personal-os'})+chr(10))"
```

## Reglas duras
- NUNCA redactes tú el brief ni lo "mejores". Si brief.py truena, manda el error en crudo por Slack y no lo sustituyas por una versión tuya. Un brief escrito a mano se ve igual de bien, se salta todos los cruces, y desde ese momento hay dos versiones de la verdad.
- NUNCA mandes correo. NUNCA mandes Slack a nadie que no sea U077GQC532M.
- No detalles nada de los dominios firewalled: el código ya los cuenta sin nombrarlos.
- Tu respuesta en el historial de la rutina: máximo dos líneas diciendo si el brief se envió y a qué hora.