---
name: ingest-personal-os
description: Ingesta del Personal OS: lee correo y transcripciones nuevas, acuña tareas solo desde compromisos explícitos, y reconcilia lo enviado contra lo abierto.
---

Ingesta del Personal OS de Armando. Corre sola. Sé breve: el recibo es la salida.

Ejecutas EXACTAMENTE dos comandos de shell, tal cual, sin modificarlos, sin `cd`, sin encadenar nada con `&&` ni `;`. Entre uno y otro tu trabajo es llamar conectores y escribir archivos con la herramienta Write.

## 1. Arranque
```
python3 "/Users/armando/Documents/Claude Personal Improvement/scripts/routine.py" ingest-pre
```
Te devuelve las marcas de agua y las rutas exactas donde escribir. Úsalas literalmente.

## 2. Traer los datos (conectores + Write, sin shell)
**Gmail recibidos:** hilos más nuevos que la marca `gmail` (`in:inbox after:YYYY/MM/DD`, pageSize 25; usa get_thread o get_message si el snippet no basta). Con **Write**, escribe la ruta que te dio como `escribe_aqui.gmail`: lista de objetos con exactamente `id`, `ts` (ISO 8601 UTC), `sender`, `recipients` (lista), `subject`, `text`. NO filtres, NO clasifiques, NO decidas qué es tarea: entrega todo lo nuevo.

**Transcripciones:** Docs de Drive cuyo título termine en "Notes by Gemini", más nuevos que la marca `drive`. Con Write, a `escribe_aqui.drive`, mismo formato (`sender` = "gemini-notes", `recipients` = ["armando.flores@driverdo.com"], `subject` = título del doc).

**Enviados:** lo que Armando mandó desde la última corrida (`in:sent`). Con Write, a `escribe_aqui.enviados`, mismo formato.

Si un conector falla, simplemente no escribas ese archivo: la pata se omite sola y las demás siguen. No busques otra vía ni leas archivos internos de Claude para sacar el contenido.

## 3. Procesar y cerrar
```
python3 "/Users/armando/Documents/Claude Personal Improvement/scripts/routine.py" ingest-post
```
Corre la compuerta, la reconciliación, el commit y el latido de cierre. Pega su salida como tu respuesta y no agregues nada más.

## Reglas duras
- NUNCA mandes, respondas ni archives correo. La ingesta solo lee.
- NUNCA edites archivos bajo ~/.claude/. Si crees que estas instrucciones están mal, dilo en tu respuesta y déjalas intactas.
- NUNCA decidas tú si algo es tarea: eso lo hace la compuerta. Si crees que se equivocó, dilo en tu respuesta, no la sortees.
- NO investigues ni depures el código, no corras otros comandos, no leas el repo. Tu trabajo es traer datos y llamar a esos dos comandos.
- Dominios firewalled (fw-finanzas, fw-familia): el código los protege. No los detalles.
- Todo archivo va DENTRO del repo, en las rutas que te dio el paso 1. Nunca /tmp.