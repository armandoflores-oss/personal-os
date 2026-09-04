---
name: brief-personal-os
description: Brief matutino del Personal OS a las 07:00 CDMX: deposita calendario en cache y renderiza con scripts/brief.py.
---

Brief matutino de Armando. Corre solo. Tu trabajo NO es redactar el brief: lo redacta un script. Tú depositas en el repo lo que viene de fuera, ejecutas el renderizador, y entregas su salida.

REPO: /Users/armando/Documents/Claude Personal Improvement

**Ejecuta los comandos EXACTAMENTE como están escritos, con rutas absolutas y `git -C`. No los combines con `cd` ni los encadenes con `&&`:** `cd <ruta> && git ...` dispara una comprobación de seguridad por los hooks del repo y detiene la corrida pidiendo aprobación que nadie puede dar.

## 0. Latido de arranque — antes de tocar cualquier conector
```
python3 "/Users/armando/Documents/Claude Personal Improvement/scripts/heartbeat.py" start brief-personal-os
```
Luego, como comando aparte:
```
git -C "/Users/armando/Documents/Claude Personal Improvement" pull --rebase
```
Si el pull falla, sigue adelante.

## 1. Depositar el calendario de hoy
Con Google Calendar, lista los eventos de HOY (America/Mexico_City) y escribe `cache/calendar/YYYY-MM-DD.json` dentro del repo: lista de objetos con exactamente start ("HH:MM" CDMX), summary, attendees (lista de correos). Sin eventos, escribe `[]`. Si el conector falla, NO escribas el archivo y registra {"ts": <ISO UTC>, "leg":"error", "source":"calendar", "error":"..."} en syncs/YYYY-MM-DD.ndjson.

## 2. Depositar transcripciones recientes
Con Drive, busca Docs cuyo título termine en "Notes by Gemini" modificados en los últimos 3 días y guarda su texto en `cache/transcripts/<id>.txt`. Si falla, sigue: el brief se rinde igual, solo cruza con menos evidencia.

## 3. Renderizar
```
python3 "/Users/armando/Documents/Claude Personal Improvement/scripts/brief.py" render
```

## 4. ENTREGAR — tres veces, ninguna opcional
**4a. En tu respuesta de la rutina.** Pega la salida COMPLETA de brief.py, literal.
**4b. Por DM de Slack** con slack_send_message: channel_id `U077GQC532M`, message = la salida completa y literal. Un DM a uno mismo NO notifica: es la copia consultable, no el aviso.
**4c. El aviso, con PushNotification.** UNA línea de menos de 200 caracteres, sin markdown, con lo accionable: cuántos pendientes abiertos y sus códigos, cuántos nuevos te requieren, cuántas juntas. Ejemplo: "Brief listo: 2 pendientes (T-3, T-4), nada nuevo, 12 juntas hoy". Es el único paso que te alcanza lejos de la Mac.

Si 4b o 4c fallan, registra {"leg":"error","source":"slack"|"push",...} en syncs/ y continúa.

## 5. Commit
```
git -C "/Users/armando/Documents/Claude Personal Improvement" add -A
```
```
git -C "/Users/armando/Documents/Claude Personal Improvement" commit -m "Brief del día"
```
No hagas push: está bloqueado.

## 6. Latido de cierre — pase lo que pase
```
python3 "/Users/armando/Documents/Claude Personal Improvement/scripts/heartbeat.py" end brief-personal-os
```

## Reglas duras — ninguna es negociable durante una corrida
- **NUNCA edites este archivo ni ningún otro bajo ~/.claude/.** Si crees que estas instrucciones están mal, dilo en tu respuesta y déjalas intactas. Una rutina que se reescribe a sí misma no tiene límites, solo sugerencias.
- **NUNCA redactes tú el brief ni lo "mejores".** Si brief.py truena, entrega el error en crudo. Un brief hecho a mano se ve igual de bien, se salta los tres cruces de supresión, y desde ahí hay dos versiones de la verdad.
- **NO leas Gmail ni canales de Slack.** El brief se rinde con el repo, el calendario y las transcripciones. Nada más.
- NUNCA mandes correo. En Slack el ÚNICO destinatario es U077GQC532M.
- No detalles nada de los dominios firewalled: el código ya los cuenta sin nombrarlos.