---
name: ingest-personal-os
description: Ingesta del Personal OS: lee correo y transcripciones nuevas, acuña tareas solo desde compromisos explícitos, y reconcilia lo enviado contra lo abierto.
---

Rutina de ingesta del Personal OS de Armando. Corre sola, sin nadie mirando. Sé breve y no expliques lo que haces: el recibo es la salida.

REPO: /Users/armando/Documents/Claude Personal Improvement
Trabaja siempre desde ahí. Todo el juicio vive en los scripts; tu único trabajo que un script no puede hacer es llamar a los conectores y entregar los items crudos como JSON.

## 0. Antes de nada
```
cd "/Users/armando/Documents/Claude Personal Improvement"
git pull --rebase 2>/dev/null || true
```

## 1. Pata de ENTRADA — Gmail
a) Lee la marca de agua:
   `python3 scripts/ingest.py watermark --source gmail`
   Si sale vacío, usa las últimas 24 horas como límite.
b) Con el conector de Gmail, busca los hilos RECIBIDOS más nuevos que esa marca
   (query tipo `in:inbox after:YYYY/MM/DD`, pageSize 25, vista MINIMAL).
   Para cada mensaje necesitas el cuerpo: usa get_thread cuando el snippet no baste.
c) Escribe un JSON en /tmp/ingest_gmail.json: una lista de objetos con exactamente
   estas llaves: id, ts (ISO 8601 UTC), sender, recipients (lista), subject, text.
   NO filtres, NO clasifiques, NO decidas qué es tarea. Entrega todo lo nuevo.
d) `python3 scripts/ingest.py run --source gmail --items /tmp/ingest_gmail.json`

## 2. Pata de ENTRADA — transcripciones
Las juntas de Armando las transcribe Gemini y aterrizan como Google Docs cuyo
título termina en "Notes by Gemini", en Drive.
a) `python3 scripts/ingest.py watermark --source drive`
b) Con el conector de Drive, lista los archivos recientes; quédate con los que
   digan "Notes by Gemini" y sean más nuevos que la marca. Lee su contenido.
c) Mismo formato JSON en /tmp/ingest_drive.json (sender = "gemini-notes",
   recipients = ["armando.flores@driverdo.com"], subject = título del doc).
d) `python3 scripts/ingest.py run --source drive --items /tmp/ingest_drive.json`

## 3. Pata de SALIDA — reconciliación
a) Con Gmail, trae lo que Armando ENVIÓ desde la última corrida (`in:sent`), mismo
   formato, en /tmp/ingest_sent.json.
b) `python3 scripts/ingest.py reconcile --sent /tmp/ingest_sent.json`
Esto cierra tareas abiertas cuando hay evidencia de que ya respondió. Cierra de
más es barato porque reabrir cuesta una palabra; cerrar en silencio no lo es.

## 4. Cierre
```
git add -A
git commit -m "Ingesta $(date +%Y-%m-%dT%H:%M) — entrada y reconciliación" || true
```
NO intentes hacer push: está bloqueado y fallar ahí no importa.

## Reglas duras
- NUNCA mandes, respondas ni archives correo. La ingesta solo lee.
- NUNCA decidas tú si algo es tarea. Eso lo hace scripts/lib/gate.py. Si crees que
  la compuerta se equivocó, NO la sortees: anótalo en el recibo y sigue.
- Dominios firewalled (fw-finanzas, fw-familia): el código ya los protege. No los
  detalles en ningún lado.
- Si un conector falla, no lo intentes por otra vía: registra la falla en
  syncs/YYYY-MM-DD.ndjson como {"ts":..., "leg":"error", "source":..., "error":...}
  y continúa con las demás patas. Una pata caída no cancela la corrida.

## Salida
Máximo cinco líneas, en español: cuántos items viste, cuántas tareas creaste (con
sus códigos), cuántas suprimiste y por qué motivo, y cuántas cerró la
reconciliación. Nada más. Los recibos completos ya quedaron en syncs/.