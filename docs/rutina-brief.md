---
name: brief-personal-os
description: Brief matutino del Personal OS a las 07:00 CDMX: deposita calendario en cache y renderiza con scripts/brief.py.
---

Brief matutino de Armando. Corre solo. Tú NO redactas el brief: lo redacta un script.

Ejecutas EXACTAMENTE dos comandos de shell, tal cual, sin modificarlos, sin `cd`, sin encadenar nada con `&&` ni `;`. Entre uno y otro tu trabajo es llamar conectores y escribir archivos con la herramienta Write.

## 1. Arranque
```
python3 "/Users/armando/Documents/Claude Personal Improvement/scripts/routine.py" brief-pre
```
Te devuelve las dos rutas donde depositar lo de fuera. Úsalas literalmente.

## 2. Depositar lo que viene de fuera (conectores + Write, sin shell)
**Calendario:** con Google Calendar lista los eventos de HOY (America/Mexico_City). Con **Write**, escribe `<escribe_calendario_en>/YYYY-MM-DD.json` (fecha de hoy en CDMX): lista de objetos con exactamente `start` ("HH:MM" CDMX), `summary`, `attendees` (lista de correos). Sin eventos, escribe `[]`.

**Transcripciones:** Docs de Drive cuyo título termine en "Notes by Gemini" modificados en los últimos 3 días. Con Write, guarda el texto de cada uno en `<escribe_transcripciones_en>/<id>.txt`. Son lo que el cruce usa para suprimir lo ya tratado en junta.

Si un conector falla, no escribas ese archivo y sigue: el brief se rinde igual, solo cruza con menos evidencia.

## 3. Renderizar y cerrar
```
python3 "/Users/armando/Documents/Claude Personal Improvement/scripts/routine.py" brief-post
```
Renderiza, commitea y cierra el latido. Su salida ES el brief.

## 4. Entregarlo — tres veces, ninguna opcional
**4a.** Pega la salida del paso 3 COMPLETA y literal como tu respuesta.
**4b.** Con slack_send_message a `U077GQC532M`: la misma salida, completa y literal. Un DM a uno mismo no notifica: es la copia consultable.
**4c.** Con PushNotification: UNA línea de menos de 200 caracteres, sin markdown, con lo accionable — pendientes abiertos y sus códigos, cuántos nuevos te requieren, cuántas juntas. Ej: "Brief listo: 2 pendientes (T-3, T-4), nada nuevo, 12 juntas hoy". Es lo único que te alcanza lejos de la Mac.

## Reglas duras
- **NUNCA redactes tú el brief ni lo "mejores".** Si el paso 3 devuelve un error, entrégalo en crudo. Un brief hecho a mano se ve igual de bien, se salta los tres cruces de supresión, y desde ahí hay dos versiones de la verdad.
- NUNCA edites archivos bajo ~/.claude/. Si crees que estas instrucciones están mal, dilo en tu respuesta y déjalas intactas.
- NO leas Gmail ni canales de Slack. NO investigues ni depures el código, no corras otros comandos.
- NUNCA mandes correo. En Slack el ÚNICO destinatario es U077GQC532M.
- No detalles nada de los dominios firewalled: el código ya los cuenta sin nombrarlos.