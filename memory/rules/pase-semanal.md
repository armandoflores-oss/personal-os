---
titulo: Pase semanal
no_weave: true
---

# Pase semanal

Viernes 18:45, después del loop. Dos trabajos sobre la misma evidencia.

## Promover correcciones repetidas

Decir lo mismo tres veces es Armando haciendo a mano lo que el sistema debería
hacer solo. El agrupador compara **raíces de palabras**, no palabras completas:
"correos" y "correo" son la misma idea, y un agrupador que no lo vea parte en dos
lo que es un racimo.

**Un commit por regla.** No es cosmético: así cualquier promoción se revierte
sin arrastrar a las demás. Si una regla salió mal, se revierte esa y punto.

El destino importa: `rules` para reglas sobre el trabajo de Armando, `instruccion`
para reglas sobre cómo debe comportarse Claude.

## Repartir mejoras por riesgo

**Bajo riesgo** es un número de una lista corta dentro de `loop.py`
(`MAX_MUTACIONES` 1–12, `VENTANA_PROPUESTA_H` 24–168). Se aplican solas, con su
commit, y aparecen como recibo en el brief. Fuera de rango, se rechazan.

Nada fuera de esa lista es bajo riesgo por más pequeño que parezca. Un "ajuste de
umbral" que pueda tocar el renderizador del brief o los permisos es estructural
con otro nombre.

**Estructural** es todo lo que toque el renderizador, otra rutina, o las
instrucciones. Va **numerado al brief**, y Armando responde `aplica 2` o
`mejora 2 nunca`.

## La regla que no se rompe

**Nunca se deja una propuesta en una carpeta que Armando tenga que abrir.** Las
colas que esperan a que alguien las visite se pudren; el brief es la única
superficie y ahí van.

Aceptar una mejora no la implementa: la marca aceptada para la siguiente sesión.
