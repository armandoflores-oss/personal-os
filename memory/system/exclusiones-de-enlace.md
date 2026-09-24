---
titulo: Exclusiones de enlazado
no_weave: true
---

# Exclusiones de enlazado

El tejedor (`scripts/weave.py`) **no toca** las cards listadas aquí: ni les
agrega enlaces, ni las enlaza desde ningún hub, ni las cuenta como huérfanas.

Para excluir una card, agrega su slug como viñeta abajo, o pon `no_weave: true`
en su frontmatter. Las dos formas valen; la lista sirve para excluir sin editar
la card, y el frontmatter para que la exclusión viaje con ella.

## Cards excluidas

- exclusiones-de-enlace

<!-- Las bóvedas firewalled no necesitan estar aquí: el tejedor solo recorre
     memory/ y nunca sale de ahí. Su ubicación no se nombra en este repo. -->
