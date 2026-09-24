---
titulo: Contrato de captura de lectura externa
no_weave: true
---

# Contrato de captura de lectura externa

Tres vías para meter algo de afuera. Las tres terminan en lo mismo.

| Vía | Cómo se dispara | Quién la corre |
|---|---|---|
| En sesión | Armando pega una liga o suelta un archivo y dice "guárdalo" | Claude, en el momento |
| Correo | Se manda a sí mismo la liga con **LEER** en el asunto | La rutina de ingesta |
| Carpeta | Deja archivos en `~/Lecturas` | La rutina de ingesta |

## La regla que las une

**El crudo se escribe una vez y no se toca más.** Va a `memory/sources/` con su
origen, su fecha y su hash. Es la evidencia: si mañana la destilación resulta
equivocada, tiene que poder leerse lo que de verdad llegó. `scripts/sources_immutable.py`
rechaza en el commit cualquier modificación, borrado o renombrado ahí.

**La destilación sí vive.** Su página en `memory/context/` resume la pieza y la
enlaza con la gente, los proyectos y los temas que toca. Esa se reescribe cuantas
veces haga falta; para eso existe.

## Detalles que importan

- **Dedupe por contenido**, no por nombre ni por URL. La misma pieza que entra
  por dos vías produce una sola fuente. El índice vive en `state/sources-index.json`.
- **El tejedor no entra a `sources/`.** Si lo hiciera, le inyectaría enlaces al
  crudo, que es justo lo prohibido. La telaraña se teje sobre lo destilado.
- **El resumen es trabajo de quien captura**, no del script. Un resumen que no
  dice nada es peor que decir "no pude destilarlo": lo segundo se puede arreglar,
  lo primero se confunde con conocimiento.
- Lo de la carpeta vigilada se mueve a `~/Lecturas/_procesados` al entrar, para
  que la carpeta sea una bandeja y no un archivero.
