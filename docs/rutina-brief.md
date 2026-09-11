---
name: brief-personal-os
description: Brief matutino del Personal OS a las 09:00 CDMX: deposita calendario en cache, renderiza con routine.py y lo entrega por Slack.
---

Brief matutino de Armando. Corre solo. Tú NO redactas el brief: lo redacta un script.

## Lo primero, y manda sobre todo lo demás
Ejecutas EXACTAMENTE dos comandos de shell, los dos de abajo, tal cual, sin modificarlos. **Ningún otro comando de shell, nunca, por ninguna razón.** No inspecciones archivos, no listes directorios, no hagas `cd`, `ls`, `cat`, `head`, `grep`, ni bucles. No verifiques tu propio trabajo con el shell.

**Si una acción te es denegada o falla: NO la reintentes. Pasa al siguiente paso.** Un paso omitido produce un brief con menos evidencia, que es correcto. Un reintento en bucle deja a Armando aprobando diálogos, que no lo es.

## 1. Arranque
```
python3 "/Users/armando/Documents/Claude Personal Improvement/scripts/routine.py" brief-pre
```
Te devuelve las dos rutas donde depositar lo de fuera. Úsalas literalmente.

## 2. Depositar lo que viene de fuera (conectores + Write, sin shell)
**Calendario:** con Google Calendar lista los eventos de HOY (America/Mexico_City). Con **Write**, escribe `<escribe_calendario_en>/YYYY-MM-DD.json` (fecha de hoy en CDMX): lista de objetos con exactamente `start` ("HH:MM" CDMX), `summary`, `attendees` (lista de correos). Sin eventos, escribe `[]`.

**Transcripciones:** Docs de Drive cuyo título termine en "Notes by Gemini" modificados en los últimos 3 días. Con Write, guarda el texto de cada uno en `<escribe_transcripciones_en>/<id>.txt`.
Esa carpeta YA contiene archivos de días anteriores. **No la revises, no la listes, no compares.** Solo escribe los que traigas de Drive; si un archivo ya existe se sobrescribe y no pasa nada.
Si Drive falla o devuelve vacío, sigue sin transcripciones: el brief se rinde igual.

## 3. Renderizar y cerrar
```
python3 "/Users/armando/Documents/Claude Personal Improvement/scripts/routine.py" brief-post
```
Su salida ES el brief.

## 4. Entregarlo — tres veces, ninguna opcional
**4a.** Pega la salida del paso 3 COMPLETA y literal como tu respuesta.
**4b.** Con slack_send_message a `U077GQC532M`: la misma salida, completa y literal.
**4c.** Con PushNotification: UNA línea de menos de 200 caracteres, sin markdown: pendientes abiertos con sus códigos, cuántos nuevos te requieren, cuántas juntas. Ej: "Brief listo: 2 pendientes (T-3, T-4), nada nuevo, 12 juntas hoy".

## Reglas duras
- **NUNCA redactes tú el brief ni lo "mejores".** Si el paso 3 devuelve un error, entrégalo en crudo. Un brief hecho a mano se ve igual de bien, se salta los tres cruces de supresión, y desde ahí hay dos versiones de la verdad.
- NUNCA edites archivos bajo ~/.claude/. Si crees que estas instrucciones están mal, dilo en tu respuesta y déjalas intactas.
- NO leas Gmail ni canales de Slack.
- NUNCA mandes correo. En Slack el ÚNICO destinatario es U077GQC532M.
- No detalles nada de los dominios firewalled: el código ya los cuenta sin nombrarlos.