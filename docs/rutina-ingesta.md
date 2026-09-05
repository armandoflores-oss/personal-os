---
name: ingest-personal-os
description: Ingesta del Personal OS: lee correo y transcripciones nuevas, acuña tareas solo desde compromisos explícitos, y reconcilia lo enviado contra lo abierto.
---

Ingesta del Personal OS de Armando. Corre sola. Sé breve: el recibo es la salida.

## Reglas de ejecución — manda sobre todo lo demás
Ejecutas EXACTAMENTE dos comandos de shell, los de abajo, tal cual. **Ningún otro comando, nunca.** No hagas `cd`, `ls`, `cat`, `head`, `grep`, ni bucles; están prohibidos por permisos y solo trabarían la corrida.

**Escribes EXACTAMENTE UN archivo con la herramienta Write. Uno solo.** Cada escritura interrumpe a Armando con un diálogo, así que juntar todo en un archivo no es una preferencia de estilo: es la diferencia entre una interrupción y tres.

**Si una acción es denegada o falla: NO la reintentes. Sigue al paso siguiente.**

## 1. Arranque
```
python3 "/Users/armando/Documents/Claude Personal Improvement/scripts/routine.py" ingest-pre
```
Te devuelve las marcas de agua y la ruta única donde escribir.

## 2. Traer todo y escribirlo UNA vez
Con los conectores, junta las tres cosas antes de escribir nada:

- **gmail** — hilos RECIBIDOS más nuevos que la marca `gmail` (`in:inbox after:YYYY/MM/DD`, pageSize 25; usa get_thread o get_message si el snippet no basta).
- **drive** — Docs cuyo título termine en "Notes by Gemini", más nuevos que la marca `drive`. Si un archivo es un acceso directo y `read_file_content` devuelve vacío, sáltalo.
- **sent** — lo que Armando ENVIÓ desde la última corrida (`in:sent`).

Ya con las tres listas en mano, escribe **una sola vez**, con Write, en la ruta que te dio `escribe_UN_archivo_aqui`, este objeto:
```json
{"gmail": [...], "drive": [...], "sent": [...]}
```
Cada item lleva exactamente: `id`, `ts` (ISO 8601 UTC), `sender`, `recipients` (lista), `subject`, `text`.
Para los de `drive`: `sender` = "gemini-notes", `recipients` = ["armando.flores@driverdo.com"], `subject` = título del doc.
Una lista vacía es válida. NO filtres, NO clasifiques, NO decidas qué es tarea: entrega todo lo nuevo.

## 3. Procesar y cerrar
```
python3 "/Users/armando/Documents/Claude Personal Improvement/scripts/routine.py" ingest-post
```
Corre la compuerta, la reconciliación, el commit y el latido. Pega su salida como tu respuesta, sin agregar nada.

## Reglas duras
- Si escribes algún evento, el actor es `system:ingest`, nunca `user`. `user` significa que lo dijo Armando con su boca, y el grader usa ese campo como verdad de campo.
- NUNCA mandes, respondas ni archives correo. La ingesta solo lee.
- NUNCA edites archivos bajo ~/.claude/. Si crees que estas instrucciones están mal, dilo en tu respuesta y déjalas intactas.
- NUNCA decidas tú si algo es tarea: eso lo hace la compuerta. Si crees que se equivocó, dilo en tu respuesta.
- NO investigues ni depures el código.
- Dominios firewalled (fw-finanzas, fw-familia): el código los protege. No los detalles.