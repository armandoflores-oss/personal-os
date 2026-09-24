---
titulo: Libro de propuestas
no_weave: true
---

# Libro de propuestas

Una propuesta es lo que el loop **sospecha** pero no puede probar. Vive en
`state/loop/propuestas.json` y aparece **solo en el brief**, en ningún otro lado.

## Las cuatro reglas

1. **Nace con fecha de vencimiento a 72 horas.** El brief la muestra con esa
   fecha y con las dos respuestas de una palabra: `<código> va` la aplica ya,
   `<código> nunca` la mata para siempre.
2. **Cualquier acción de Armando sobre el item es un veto.** No hay que
   preguntarle: que se haya metido ya dice todo lo que hacía falta saber. No
   importa qué hizo — una nota, un cambio de fecha, reasignarla.
3. **El veto es permanente.** La entrada queda vetada para siempre y ese item
   no se vuelve a proponer, aunque la evidencia reaparezca. Probado: reproponer
   algo vetado devuelve `vetada para siempre`.
4. **Lo firewalled nunca vence.** Espera indefinidamente a que él lo toque, y en
   el brief aparece **solo como conteo**: sin código, sin título, sin fecha.
   Una propuesta retenida que muestre su título es la misma fuga que mostrar la
   card, solo que en otra sección.

## Cuándo corre

Dentro de `loop.py apply` (antes de evaluar nada nuevo) y en `brief-pre`, para
que el brief muestre el estado de hoy y no el de anoche. No es un comando
aparte a propósito: así no cuesta aprobaciones nuevas.

## Lo que vence se cierra con recibo

Con su evidencia y su deshacer en la misma línea:
`T-34 cerrada al vencer su propuesta · sin movimiento en dos semanas` /
`↩︎ reábrela con T-34 no`.
