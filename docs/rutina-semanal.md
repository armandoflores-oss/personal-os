---
name: semanal-personal-os
description: Pase semanal: promueve correcciones repetidas a reglas y reparte mejoras por riesgo.
---

Pase semanal del Personal OS de Armando. Viernes, después del loop nocturno.

## Reglas de ejecución
Ejecutas los comandos de abajo tal cual. **Ningún otro comando de shell.** Nada de `cd`, `ls`, `cat`, `grep`. Escribes como mucho **dos archivos** con Write. Si algo falla o te es denegado, NO reintentes.

## 1. Agrupar las correcciones de la semana
```
python3 "/Users/armando/Documents/Claude Personal Improvement/scripts/weekly.py" cluster
```
Devuelve racimos (correcciones que se parecen) y sueltas. El agrupador compara palabras; **tú además revisa las sueltas** y junta las que digan lo mismo con otras palabras — eso el script no lo puede ver.

## 2. Escribir las reglas
Para cada racimo que de verdad sea **una regla durable** —no un defecto puntual, no un hecho de un cliente— escribe la regla. Un racimo de defectos del clasificador no es una regla: es un bug, y ese va como mejora en el paso 4.

Con Write, en `/Users/armando/Documents/Claude Personal Improvement/state/loop/reglas-<FECHA>.json`:
```json
{"reglas":[{"titulo":"...","veces":3,"destino":"rules|instruccion",
            "cuerpo":"markdown: qué regla es, cuándo aplica, y la excepción si la hay"}]}
```
- `destino: rules` para reglas sobre **el trabajo de Armando** (qué es tarea, cómo se cotiza, qué va al brief).
- `destino: instruccion` para reglas sobre **cómo debe comportarse Claude** (tono, permisos, cómo correr comandos).
- El `cuerpo` lo lee Armando dentro de seis meses sin este contexto. Escríbelo para él: la regla, cuándo aplica, y qué la rompe.

Luego:
```
python3 "/Users/armando/Documents/Claude Personal Improvement/scripts/weekly.py" promote --reglas "/Users/armando/Documents/Claude Personal Improvement/state/loop/reglas-<FECHA>.json"
```
Hace **un commit por regla**, a propósito: así cualquiera se revierte sin arrastrar a las demás.

## 3. Pensar qué mejoraría el sistema
Mira la semana: qué se suprimió mal, qué se cerró de más, dónde Armando tuvo que intervenir. De ahí salen las mejoras.

## 4. Repartir las mejoras por riesgo
Con Write, en `.../state/loop/mejoras-<FECHA>.json`:
```json
{"mejoras":[
  {"constante":"MAX_MUTACIONES","valor":8,"por":"por qué, con el dato que lo justifica"},
  {"titulo":"...","toca":"qué archivo o rutina","por":"por qué vale la pena"}
]}
```
- **Bajo riesgo** = un número de la lista permitida dentro de `loop.py` (`MAX_MUTACIONES` 1-12, `VENTANA_PROPUESTA_H` 24-168). Se aplican solas, cada una con su commit, y salen como recibo en el brief. Nada fuera de esa lista es bajo riesgo, por más pequeño que parezca.
- **Estructural** = cualquier cosa que toque el renderizador del brief, otra rutina, o las instrucciones de Armando. Van numeradas al brief y él las acepta con `aplica 2` o las mata con `mejora 2 nunca`. **Nunca las dejes en una carpeta que él tenga que abrir.**

```
python3 "/Users/armando/Documents/Claude Personal Improvement/scripts/weekly.py" upgrade --propuestas "/Users/armando/Documents/Claude Personal Improvement/state/loop/mejoras-<FECHA>.json"
```

## Salida
Máximo cinco líneas: cuántas correcciones viste, qué reglas promoviste, qué ajustes se aplicaron solos y qué mejoras quedaron propuestas. Nada más.

## Reglas duras
- Una semana sin patrones es una semana normal: si no hay racimo real, no inventes una regla. Promover ruido a regla es peor que no promover nada.
- NUNCA edites reglas existentes: si una quedó mal, propón la corrección como mejora estructural.
- NUNCA mandes correo ni mensajes. NUNCA toques ~/.claude/ salvo vía `promote --destino instruccion`.
- No construyas ningún reporte semanal de aprendizaje. El crecimiento se ve en `memory/changelog.md`.