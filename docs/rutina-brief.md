---
name: brief-personal-os
description: Brief matutino del Personal OS a las 07:00 CDMX: deposita calendario en cache y renderiza con scripts/brief.py.
---

Brief matutino de Armando. Corre solo. Tu trabajo NO es redactar el brief: lo redacta un script. Tú depositas en el repo lo que viene de fuera, ejecutas el renderizador, y entregas su salida.

REPO: /Users/armando/Documents/Claude Personal Improvement

## 0. Latido de arranque (ANTES de tocar cualquier conector)
```
cd "/Users/armando/Documents/Claude Personal Improvement"
python3 -c "import json,datetime,pathlib; d=datetime.datetime.now(datetime.timezone.utc); p=pathlib.Path('syncs')/f'{d.date()}.ndjson'; p.parent.mkdir(exist_ok=True); f=open(p,'a'); f.write(json.dumps({'ts':d.isoformat(timespec='seconds'),'leg':'heartbeat','stage':'start','task':'brief-personal-os'})+chr(10))"
git pull --rebase 2>/dev/null || true
```

## 1. Depositar el calendario de hoy
Con Google Calendar, lista los eventos de HOY (America/Mexico_City) y escribe `cache/calendar/YYYY-MM-DD.json`: lista de objetos con exactamente start ("HH:MM" CDMX), summary, attendees (lista de correos). Sin eventos, escribe `[]`. Si el conector falla, NO escribas el archivo y registra {"ts": <ISO UTC>, "leg":"error", "source":"calendar", "error":"..."} en syncs/YYYY-MM-DD.ndjson.

## 2. Depositar transcripciones recientes
Con Drive, busca Docs cuyo título termine en "Notes by Gemini" modificados en los últimos 3 días y guarda su texto en `cache/transcripts/<id>.txt`. Si falla, sigue.

## 3. Renderizar
```
cd "/Users/armando/Documents/Claude Personal Improvement"
python3 scripts/brief.py render
```

## 4. ENTREGAR — tres veces, ninguna opcional
**4a. En tu respuesta de la rutina.** Pega la salida COMPLETA de brief.py, literal.
**4b. Por DM de Slack** con slack_send_message: channel_id `U077GQC532M`, message = la salida completa y literal. Un DM a uno mismo NO genera notificación: es el archivo consultable, no el aviso.
**4c. El aviso, con PushNotification.** UNA línea de menos de 200 caracteres, sin markdown, con lo accionable del día: cuántos pendientes abiertos, cuántos nuevos te requieren, cuántas juntas. Ejemplo: "Brief listo: 2 pendientes (T-3, T-4), nada nuevo, 12 juntas hoy". Este es el único paso que de verdad te alcanza si no estás frente a la Mac.

Si 4b o 4c fallan, registra {"leg":"error","source":"slack"|"push",...} en syncs/ y continúa: el brief ya quedó en briefs/ y en tu respuesta.

## 5. Commit
```
git add -A && git commit -m "Brief $(date +%Y-%m-%d)" || true
```
No hagas push: está bloqueado.

## 6. Latido de cierre — pase lo que pase
```
python3 -c "import json,datetime,pathlib; d=datetime.datetime.now(datetime.timezone.utc); p=pathlib.Path('syncs')/f'{d.date()}.ndjson'; f=open(p,'a'); f.write(json.dumps({'ts':d.isoformat(timespec='seconds'),'leg':'heartbeat','stage':'end','task':'brief-personal-os'})+chr(10))"
```

## Reglas duras — ninguna es negociable durante una corrida
- **NUNCA edites este archivo ni ningún otro bajo ~/.claude/.** Si crees que estas instrucciones están mal, dilo en tu respuesta y déjalas intactas. Una rutina que se reescribe a sí misma no tiene límites, solo sugerencias. (Ya está prohibido por permisos; esto es el porqué.)
- **NUNCA redactes tú el brief ni lo "mejores".** Si brief.py truena, entrega el error en crudo. Un brief escrito a mano se ve igual de bien, se salta los tres cruces de supresión, y desde ahí hay dos versiones de la verdad.
- **NO leas Gmail ni canales de Slack.** El brief se rinde con el repo, el calendario y las transcripciones. Nada más.
- NUNCA mandes correo. En Slack, el ÚNICO destinatario es U077GQC532M.
- No detalles nada de los dominios firewalled: el código ya los cuenta sin nombrarlos.