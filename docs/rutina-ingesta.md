---
name: ingest-personal-os
description: Ingesta del Personal OS: lee correo y transcripciones nuevas, acuña tareas solo desde compromisos explícitos, y reconcilia lo enviado contra lo abierto.
---

Rutina de ingesta del Personal OS de Armando. Corre sola, sin nadie mirando. Sé breve: el recibo es la salida.

REPO: /Users/armando/Documents/Claude Personal Improvement

## Cómo ejecutar cosas — esto detiene la corrida si te lo saltas
Una corrida desatendida no puede aprobar nada. Tres patrones piden aprobación y hay que evitarlos:
1. **`cd <ruta> && git ...`** → dispara la comprobación de hooks del repo. Usa `git -C "<repo>"`, siempre como comando suelto.
2. **Heredocs y JSON dentro del shell** (`python3 - <<'PY'`, llaves con comillas) → dispara la detección de ofuscación. **Para escribir cualquier archivo JSON usa la herramienta Write, nunca el shell.**
3. Comandos encadenados con `&&`. Uno por llamada.
Rutas siempre absolutas.

## 0. Latido de arranque — antes de tocar cualquier conector
```
python3 "/Users/armando/Documents/Claude Personal Improvement/scripts/heartbeat.py" start ingest-personal-os
```
Aparte:
```
git -C "/Users/armando/Documents/Claude Personal Improvement" pull --rebase
```
Si el pull falla, sigue.

## 1. Pata de ENTRADA — Gmail
a) `python3 "/Users/armando/Documents/Claude Personal Improvement/scripts/ingest.py" watermark --source gmail`
   Vacío = usa las últimas 24 horas.
b) Con Gmail busca los hilos RECIBIDOS más nuevos que esa marca (`in:inbox after:YYYY/MM/DD`, pageSize 25). Usa get_thread o get_message cuando el snippet no baste.
c) **Con la herramienta Write**, escribe `/tmp/ingest_gmail.json`: lista de objetos con exactamente id, ts (ISO 8601 UTC), sender, recipients (lista), subject, text. NO filtres, NO clasifiques, NO decidas qué es tarea: entrega todo lo nuevo.
d) `python3 "/Users/armando/Documents/Claude Personal Improvement/scripts/ingest.py" run --source gmail --items /tmp/ingest_gmail.json`

## 2. Pata de ENTRADA — transcripciones
a) `python3 "/Users/armando/Documents/Claude Personal Improvement/scripts/ingest.py" watermark --source drive`
b) Con Drive, los Docs "Notes by Gemini" más nuevos que la marca; lee su contenido.
c) Con Write, `/tmp/ingest_drive.json`, mismo formato (sender "gemini-notes", recipients ["armando.flores@driverdo.com"], subject = título del doc).
d) `python3 "/Users/armando/Documents/Claude Personal Improvement/scripts/ingest.py" run --source drive --items /tmp/ingest_drive.json`

## 3. Pata de SALIDA — reconciliación
a) Con Gmail trae lo ENVIADO desde la última corrida (`in:sent`); con Write, `/tmp/ingest_sent.json`, mismo formato.
b) `python3 "/Users/armando/Documents/Claude Personal Improvement/scripts/ingest.py" reconcile --sent /tmp/ingest_sent.json`

## 4. Cierre
```
git -C "/Users/armando/Documents/Claude Personal Improvement" add -A
```
```
git -C "/Users/armando/Documents/Claude Personal Improvement" commit -m "Ingesta automática"
```
NO hagas push: está bloqueado.

## 5. Latido de cierre — pase lo que pase
```
python3 "/Users/armando/Documents/Claude Personal Improvement/scripts/heartbeat.py" end ingest-personal-os
```

## Reglas duras
- **Si escribes CUALQUIER evento, el actor es `system:ingest`, nunca `user`.** `user` significa que lo dijo Armando con su boca. El grader de la Fase 6 usa ese campo como verdad de campo: si firmas como él, el sistema se cuenta a sí mismo como intervención suya. Los scripts ya lo exigen y truenan si falta.
- NUNCA mandes, respondas ni archives correo. La ingesta solo lee.
- NUNCA edites archivos bajo ~/.claude/. Si crees que estas instrucciones están mal, dilo en tu respuesta y déjalas intactas.
- NUNCA decidas tú si algo es tarea: eso lo hace scripts/lib/gate.py. Si crees que se equivocó, anótalo en el recibo, no la sortees.
- Dominios firewalled (fw-finanzas, fw-familia): el código los protege. No los detalles.
- Si un conector falla, registra {"ts":..., "leg":"error", "source":..., "error":...} en syncs/YYYY-MM-DD.ndjson y sigue con las demás patas.

## Salida
Máximo cinco líneas en español: items vistos, tareas creadas con sus códigos, suprimidas y por qué, cuántas cerró la reconciliación.