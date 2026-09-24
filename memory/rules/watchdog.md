---
titulo: El watchdog
no_weave: true
---

# El watchdog

Vigila que cada productor y **cada etapa dentro de cada productor** esté
haciendo su trabajo. El manifiesto vive en `config/manifiesto.json`: una etapa
que no está ahí no se vigila, y borrar una línea de ahí se ve en el diff.

## Las cuatro reglas que lo definen

**Siempre sale con código 0.** Un watchdog que tumba la tubería que vigila es
peor que no tener watchdog: la primera vez que rompe un commit, alguien lo apaga
y nadie lo vuelve a prender.

**Un check que truena reporta ÁMBAR con su error.** Nunca desaparece callado.
Un check roto que no se ve equivale a uno que dice "verde", y ese es el modo de
falla que deja a un sistema muerto pareciendo sano.

**La frescura sale del contenido, nunca del `mtime`.** El brief declara su fecha
en el encabezado, las marcas de agua traen su timestamp, el changelog sus
`## YYYY-MM-DD`, los recibos su `ts`. Un `touch`, un `git checkout` o un respaldo
mueven la fecha del archivo sin que nada haya corrido.

**Sabe de fines de semana.** Las rutinas corren de lunes a viernes; alarmar un
domingo enseña a ignorar la alarma, y una alarma que se ignora ya no es alarma.

## Aserciones con nombre

Cada etapa obligatoria afirma **su propia línea**: `heartbeat/end/ingest-personal-os`,
`tejido`, `loop`, `outbound`. Si la línea falta más de ~26 horas hábiles, ámbar.
Verificar por ausencia de errores no sirve: un productor que no corrió tampoco
falla.

## Estado aparcado

Lo que deliberadamente no existe —el destilador y el courier de la Fase 4— está
**aparcado** con razón y fecha de revisión, no en ámbar. Pero la fecha vence: al
llegar, se vuelve ámbar sola. Aparcar algo sin fecha es olvidarlo con estilo.

## En el brief

Banda **solo cuando algo no está verde**. El brief no repite la lógica del
watchdog: le pregunta. Dos verdades sobre lo mismo se separan.
