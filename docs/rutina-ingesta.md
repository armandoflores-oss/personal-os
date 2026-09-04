---
name: ingest-personal-os
description: Ingesta del Personal OS: lee correo y transcripciones nuevas, acuña tareas solo desde compromisos explícitos, y reconcilia lo enviado contra lo abierto.
---

Rutina de ingesta del Personal OS de Armando. Corre sola, sin nadie mirando. Sé breve: el recibo es la salida.

REPO: /Users/armando/Documents/Claude Personal Improvement
Todo el juicio vive en los scripts. Tu único trabajo que un script no puede hacer es llamar a los conectores y entregar los items crudos como JSON.

**Ejecuta los comandos EXACTAMENTE como están escritos, con rutas absolutas y `git -C`. No los combines con `cd` ni los encadenes con `&&`:** `cd <ruta> && git ...` dispara una comprobación de seguridad por los hooks del repo y detiene la corrida pidiendo aprobación que nadie puede dar.

## 0. Latido de arranque — antes de tocar cualquier conector
```
python3 "/Users/armando/Documents/Claude Personal Improvement/scripts/heartbeat.py" start ingest-personal-os
```
Luego, como comando aparte:
```
git -C "/Users/armando/Documents/Claude Personal Improvement" pull --rebase
```
Si el pull falla, sigue adelante: no es motivo para abortar.

## 1. Pata de ENTRADA — Gmail
a) `python3 "/Users/armando/Documents/Claude Personal Improvement/scripts/ingest.py" watermark --source gmail`
   Si sale vacío, usa las últimas 24 horas como límite.
b) Con el conector de Gmail, busca los hilos RECIBIDOS más nuevos que esa marca (`in:inbox after:YYYY/MM/DD`, pageSize 25, vista MINIMAL). Usa get_thread o get_message cuando el snippet no baste para tener el cuerpo.
c) Escribe /tmp/ingest_gmail.json: lista de objetos con exactamente id, ts (ISO 8601 UTC), sender, recipients (lista), subject, text. NO filtres, NO clasifiques, NO decidas qué es tarea. Entrega todo lo nuevo.
d) `python3 "/Users/armando/Documents/Claude Personal Improvement/scripts/ingest.py" run --source gmail --items /tmp/ingest_gmail.json`

## 2. Pata de ENTRADA — transcripciones
Las juntas las transcribe Gemini como Google Docs cuyo título termina en "Notes by Gemini".
a) `python3 "/Users/armando/Documents/Claude Personal Improvement/scripts/ingest.py" watermark --source drive`
b) Con Drive, lista los recientes, quédate con los "Notes by Gemini" más nuevos que la marca y lee su contenido.
c) Mismo formato en /tmp/ingest_drive.json (sender "gemini-notes", recipients ["armando.flores@driverdo.com"], subject = título del doc).
d) `python3 "/Users/armando/Documents/Claude Personal Improvement/scripts/ingest.py" run --source drive --items /tmp/ingest_drive.json`

## 3. Pata de SALIDA — reconciliación
a) Con Gmail, trae lo que Armando ENVIÓ desde la última corrida (`in:sent`), mismo formato, en /tmp/ingest_sent.json.
b) `python3 "/Users/armando/Documents/Claude Personal Improvement/scripts/ingest.py" reconcile --sent /tmp/ingest_sent.json`
Cierra tareas con evidencia de que ya respondió. Cerrar de más es barato: reabrir cuesta una palabra. Cerrar en silencio no lo es.

## 4. Cierre
```
git -C "/Users/armando/Documents/Claude Personal Improvement" add -A
```
```
git -C "/Users/armando/Documents/Claude Personal Improvement" commit -m "Ingesta automática"
```
NO hagas push: está bloqueado y fallar ahí no importa.

## 5. Latido de cierre — pase lo que pase, aunque alguna pata haya fallado
```
python3 "/Users/armando/Documents/Claude Personal Improvement/scripts/heartbeat.py" end ingest-personal-os
```

## Reglas duras
- NUNCA mandes, respondas ni archives correo. La ingesta solo lee.
- NUNCA edites archivos bajo ~/.claude/ — ni estas instrucciones ni los ajustes. Si crees que están mal, dilo en tu respuesta y déjalas intactas.
- NUNCA decidas tú si algo es tarea. Eso lo hace scripts/lib/gate.py. Si crees que la compuerta se equivocó, NO la sortees: anótalo en el recibo.
- Dominios firewalled (fw-finanzas, fw-familia): el código ya los protege. No los detalles.
- Si un conector falla, no busques otra vía: registra {"ts":..., "leg":"error", "source":..., "error":...} en syncs/YYYY-MM-DD.ndjson y sigue con las demás patas.

## Salida
Máximo cinco líneas en español: items vistos, tareas creadas con sus códigos, suprimidas y por qué motivo, y cuántas cerró la reconciliación.