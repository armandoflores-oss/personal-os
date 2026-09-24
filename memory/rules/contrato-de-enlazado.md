---
titulo: Contrato de enlazado de la memoria
no_weave: true
---

# Contrato de enlazado de la memoria

Toda escritura automática en `memory/` **deja la telaraña íntegra**. No es
cortesía: una card inalcanzable es una card que no existe, y una web que se
erosiona de a poco no avisa cuándo dejó de servir.

## Quién teje

`scripts/weave.py`. Corre solo al final de cada ingesta (`routine.py ingest-post`).
Nadie enlaza a mano: lo hecho a mano no sobrevive a la card número mil.

## Las reglas que el tejedor respeta

1. **Idempotencia.** Correrlo dos veces no cambia nada. Los enlaces inline solo
   se agregan a una mención desnuda, y el bloque `Relacionado` vive entre
   marcadores y se regenera entero en vez de acumularse.
2. **Jamás un nombre de pila suelto.** "Marcelo" es una palabra; "Marcelo Treviño"
   es una persona. Enlazar nombres de pila convierte cada mención de una palabra
   común en una arista falsa, y el grafo deja de significar algo.
3. **Exclusiones.** Una card listada en `memory/system/exclusiones-de-enlace.md`
   o con `no_weave: true` en su frontmatter no se toca, no se enlaza y no cuenta
   como huérfana.
4. **Topes.** Máximo 6 enlaces inline y 8 en el bloque `Relacionado` por card.
   La densidad va en los hubs; una card que enlaza a todo no dice nada.
5. **Alias saneados.** Un título puede traer `[EXTERNAL]`, pipes o saltos de
   línea. Dentro de `[[slug|alias]]` esos caracteres rompen el enlace y en
   Obsidian se ve roto. Se limpian antes de usarlos.
6. **Nunca sale de `memory/`.** Las bóvedas firewalled no son asunto suyo.

## Cobertura garantizada, no esperada

Los hubs de entidad dan significado pero solo cubren lo que mencionan. Por eso
el tejedor genera además **índices por carpeta** —proyectos, reglas, contexto—
siempre completos y enlazados desde `home`. Esa es la red que garantiza que
ninguna card quede inalcanzable, hoy y cuando haya mil.

Hubs e índices son **derivados**: se regeneran enteros en cada corrida. No los
edites a mano; el siguiente tejido borra el cambio.

## Cómo verificar que sigue sano

```
python3 "/Users/armando/Documents/Claude Personal Improvement/scripts/weave.py" --dry-run
```
Debe reportar cero cambios sobre un árbol ya tejido. Si reporta cambios, alguien
escribió sin tejer.
