---
name: loop-personal-os
description: Loop nocturno: junta evidencia, clasifica, aplica con guardarraíles y califica el día.
---

Loop nocturno del Personal OS de Armando. Corre solo, después de la última ingesta del día y antes del brief de mañana.

## Reglas de ejecución
Ejecutas EXACTAMENTE los tres comandos de abajo, tal cual. **Ningún otro comando de shell.** Nada de `cd`, `ls`, `cat`, `grep`, ni bucles: están prohibidos por permisos. Escribes **un solo archivo**, con la herramienta Write. Si algo falla o te es denegado, NO reintentes: pasa al paso siguiente.

## 1. Preparar — la evidencia la junta el script, no tú
```
python3 "/Users/armando/Documents/Claude Personal Improvement/scripts/loop.py" prepare
```
Te dice dónde quedó el archivo de candidatos. Léelo con la herramienta Read.

## 2. Juzgar — este es tu único trabajo, y es clasificar
Para cada candidato, decide **una sola cosa**: qué tan fuerte es la evidencia que el script ya juntó. No busques evidencia nueva, no consultes conectores, no abras el correo. Solo clasificas lo que tienes enfrente.

- **`dura`** — la evidencia dice que el asunto YA se resolvió, sin ambigüedad. Ejemplos: Armando dijo con sus palabras que quedó; la junta registra que se cerró; alguien más lo tomó y lo terminó. Cerrar de más es barato porque reabrir cuesta una palabra, pero cerrar sin base destruye la confianza en todo el tablero.
- **`blanda`** — parece resuelto pero podría no estarlo. Sin movimiento en dos semanas, o una mención que apunta en esa dirección sin confirmarlo. Se vuelve propuesta: se aplica sola en 72 horas si Armando no dice nada.
- **`ninguna`** — la evidencia no dice nada útil. Es la respuesta correcta la mayoría de las veces. **Ante la duda, `ninguna`.**

Con Write, escribe `/Users/armando/Documents/Claude Personal Improvement/state/loop/decisiones-<FECHA>.json` (la fecha del archivo de candidatos):
```json
{"decisiones": [{"task_id": "...", "clase": "dura|blanda|ninguna", "evidencia": "una línea: por qué, citando lo que viste"}]}
```
El campo `evidencia` es lo que Armando va a leer mañana junto al cierre. Escríbelo para él: qué pasó y de dónde lo sabes. "Cerrada por el loop" no sirve.

## 3. Aplicar y calificar
```
python3 "/Users/armando/Documents/Claude Personal Improvement/scripts/loop.py" apply --decisiones "/Users/armando/Documents/Claude Personal Improvement/state/loop/decisiones-<FECHA>.json"
```
```
python3 "/Users/armando/Documents/Claude Personal Improvement/scripts/loop.py" grade
```
El `apply` tiene guardarraíles que tú no puedes sortear y que están ahí a propósito: valida cada id contra el estado real, degrada a propuesta cualquier cosa firewalled, corta en 6 mutaciones por noche, y sella el archivo para que no pueda aplicarse dos veces. Si rechaza algo, eso es el sistema funcionando, no un error que haya que arreglar.

## Salida
Máximo cuatro líneas: cuántos candidatos viste, cuántos clasificaste duro/blando/ninguno, qué cerró el apply y qué rechazó, y la calificación del día. Nada más.

## Reglas duras
- NUNCA cierres nada tú mismo con `task.py` ni con `reply.py`. Tu única salida es el archivo de decisiones.
- NUNCA mandes correo ni mensajes.
- NUNCA edites archivos bajo ~/.claude/ ni bajo memory/sources/.
- Dominios firewalled: el código los degrada solo. No los detalles en tu salida.
- Si el archivo de candidatos viene vacío, dilo en una línea y termina. Una noche sin nada que cerrar es una noche normal.