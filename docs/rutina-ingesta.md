---
name: ingest-personal-os
description: Ingesta del Personal OS: lee correo y transcripciones nuevas, acuña tareas solo desde compromisos explícitos, y reconcilia lo enviado contra lo abierto.
---

Rutina de ingesta del Personal OS de Armando. Corre sola, sin nadie mirando. Sé breve: el recibo es la salida.

REPO: /Users/armando/Documents/Claude Personal Improvement

## Cómo ejecutar cosas — saltarte esto detiene la corrida
Una corrida desatendida no puede aprobar nada, y hay cuatro cosas que piden aprobación:
1. **`cd <ruta> && git ...`** → comprobación de hooks del repo. Usa `git -C "<repo>"` como comando suelto.
2. **Heredocs y JSON en el shell** (`python3 - <<'PY'`, llaves con comillas) → detección de ofuscación. **Escribe archivos con la herramienta Write, nunca con el shell.**
3. **Comandos encadenados con `&&` o `;`.** Uno por llamada.
4. **Cualquier ruta fuera del repo, incluido /tmp** → "path is outside allowed working directories". TODO archivo intermedio va en `cache/tmp/` DENTRO del repo (ya está en .gitignore).
Rutas siempre absolutas y entre comillas: el repo tiene espacios en el nombre.

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
c) **Con la herramienta Write**, escribe `/Users/armando/Documents/Claude Personal Improvement/cache/tmp/ingest_gmail.json`: lista de objetos con exactamente id, ts (ISO 8601 UTC), sender, recipients (lista), subject, text. NO filtres, NO clasifiques, NO decidas qué es tarea: entrega todo lo nuevo.
d) `python3 "/Users/armando/Documents/Claude Personal Improvement/scripts/ingest.py" run --source gmail --items "/Users/armando/Documents/Claude Personal Improvement/cache/tmp/ingest_gmail.json"`

## 2. Pata de ENTRADA — transcripciones
a) `python3 "/Users/armando/Documents/Claude Personal Improvement/scripts/ingest.py" watermark --source drive`
b) Con Drive, los Docs "Notes by Gemini" más nuevos que la marca; lee su contenido.
c) Con Write, `/Users/armando/Documents/Claude Personal Improvement/cache/tmp/ingest_drive.json`, mismo formato (sender "gemini-notes", recipients ["armando.flores@driverdo.com"], subject = título del doc).
d) `python3 "/Users/armando/Documents/Claude Personal Improvement/scripts/ingest.py" run --source drive --items "/Users/armando/Documents/Claude Personal Improvement/cache/tmp/ingest_drive.json"`

## 3. Pata de SALIDA — reconciliación
a) Con Gmail trae lo ENVIADO desde la última corrida (`in:sent`); con Write, `/Users/armando/Documents/Claude Personal Improvement/cache/tmp/ingest_sent.json`, mismo formato.
b) `python3 "/Users/armando/Documents/Claude Personal Improvement/scripts/ingest.py" reconcile --sent "/Users/armando/Documents/Claude Personal Improvement/cache/tmp/ingest_sent.json"`

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
- **Si escribes CUALQUIER evento, el actor es `system:ingest`, nunca `user`.** `user` significa que lo dijo Armando con su boca. El grader de la Fase 6 usa ese campo como verdad de campo: si firmas como él, el sistema se cuenta a sí mismo como intervención suya. Los scripts lo exigen y truenan si falta.
- NUNCA mandes, respondas ni archives correo. La ingesta solo lee.
- NUNCA edites archivos bajo ~/.claude/. Si crees que estas instrucciones están mal, dilo en tu respuesta y déjalas intactas.
- NUNCA decidas tú si algo es tarea: eso lo hace scripts/lib/gate.py. Si crees que se equivocó, anótalo en el recibo, no la sortees.
- NO investigues ni depures el código. Si un script falla, reporta su salida en crudo y sigue con las demás patas. Tu trabajo es correr la tubería, no arreglarla.
- Dominios firewalled (fw-finanzas, fw-familia): el código los protege. No los detalles.
- Si un conector falla, registra {"ts":..., "leg":"error", "source":..., "error":...} en syncs/YYYY-MM-DD.ndjson y sigue.

## Salida
Máximo cinco líneas en español: items vistos, tareas creadas con sus códigos, suprimidas y por qué, cuántas cerró la reconciliación.