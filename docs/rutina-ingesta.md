---
name: ingest-personal-os
description: Ingesta del Personal OS: lee correo y transcripciones nuevas, acuña tareas solo desde compromisos explícitos, y reconcilia lo enviado contra lo abierto.
---

Ingesta del Personal OS de Armando. Corre sola. Sé breve: el recibo es la salida.

## Reglas de ejecución — manda sobre todo lo demás
Ejecutas EXACTAMENTE los comandos de abajo, tal cual. **Ningún otro comando de shell, nunca.** No hagas `cd`, `ls`, `cat`, `head`, `grep`, ni bucles: están prohibidos por permisos y solo trabarían la corrida.

**Escribes archivos SOLO con la herramienta Write, y solo los que se indican.** Cada escritura interrumpe a Armando con un diálogo, así que no escribas de más.

**Si una acción es denegada o falla: NO la reintentes. Pasa al paso siguiente.**

## 1. Arranque
```
python3 "/Users/armando/Documents/Claude Personal Improvement/scripts/routine.py" ingest-pre
```
Devuelve las marcas de agua y la ruta única donde escribir.

## 2. Traer todo y escribirlo UNA vez
Con los conectores, junta las tres cosas antes de escribir nada:

- **gmail** — hilos RECIBIDOS más nuevos que la marca `gmail` (`in:inbox after:YYYY/MM/DD`, pageSize 25; usa get_thread o get_message si el snippet no basta).
- **drive** — Docs cuyo título termine en "Notes by Gemini", más nuevos que la marca `drive`. Si un archivo es un acceso directo y devuelve vacío, sáltalo.
- **sent** — lo que Armando ENVIÓ desde la última corrida (`in:sent`).

Con Write, una sola vez, en la ruta que te dio `escribe_UN_archivo_aqui`:
```json
{"gmail": [...], "drive": [...], "sent": [...]}
```
Cada item lleva exactamente: `id`, `ts` (ISO 8601 UTC), `sender`, `recipients` (lista), `subject`, `text`. Para los de `drive`: `sender` = "gemini-notes", `recipients` = ["armando.flores@driverdo.com"], `subject` = título del doc. Lista vacía es válida. NO filtres ni clasifiques: entrega todo lo nuevo.

## 3. Vía de captura por correo — lecturas que Armando se manda a sí mismo
Busca en Gmail los correos **enviados por Armando a sí mismo** cuyo asunto contenga la palabra **LEER** (`from:me to:me subject:LEER`), más nuevos que la marca `gmail`.

Para cada uno, por cada liga que traiga en el cuerpo:
1. Trae el contenido de la liga con WebFetch. Si falla o la página no se deja leer, sáltala y sigue con la siguiente; no insistas.
2. Con Write, guarda el texto crudo en `/Users/armando/Documents/Claude Personal Improvement/cache/tmp/lectura.txt`.
3. Escribe un resumen honesto de 3 a 6 líneas: qué dice y por qué le importa a Armando dado su contexto (traslados de vehículos, sus clientes, sus deals). Si no puedes resumirlo con sustancia, di eso en el resumen en vez de inventar.
4. Captúralo:
```
python3 "/Users/armando/Documents/Claude Personal Improvement/scripts/capture_source.py" add --url "<liga>" --texto "/Users/armando/Documents/Claude Personal Improvement/cache/tmp/lectura.txt" --titulo "<título real de la pieza>" --resumen "<tu resumen>"
```
El script guarda el crudo, deduplica por contenido y arma la página destilada enlazada. Si dice `duplicado`, esa lectura ya estaba: sigue sin hacer nada más.

## 4. Procesar y cerrar
```
python3 "/Users/armando/Documents/Claude Personal Improvement/scripts/routine.py" ingest-post
```
Corre la compuerta, la reconciliación, la carpeta vigilada, el tejido, el commit y el push. Pega su salida como tu respuesta, sin agregar nada.

## Reglas duras
- Si escribes algún evento, el actor es `system:ingest`, nunca `user`. `user` significa que lo dijo Armando con su boca, y el grader usa ese campo como verdad de campo.
- NUNCA mandes, respondas ni archives correo. La ingesta solo lee.
- NUNCA edites nada bajo `memory/sources/`: el material crudo es inmutable y el hook lo rechaza.
- NUNCA edites archivos bajo ~/.claude/. Si crees que estas instrucciones están mal, dilo en tu respuesta y déjalas intactas.
- NUNCA decidas tú si algo es tarea: eso lo hace la compuerta.
- NO investigues ni depures el código.
- Dominios firewalled (fw-finanzas, fw-familia): el código los protege. No los detalles.