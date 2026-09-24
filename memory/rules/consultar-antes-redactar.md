---
titulo: Consultar la wiki antes de redactar
no_weave: true
---

# Consultar la wiki antes de redactar

Todo productor recurrente tiene el mismo primer paso: **antes de redactar,
consultar qué sabe la wiki sobre la gente, las organizaciones y los temas
involucrados, y usarlo.**

## Dónde está aplicado

| Productor | Cómo |
|---|---|
| Cualquier sesión (correos, mensajes, decks, cotizaciones, memos) | `~/.claude/CLAUDE.md` lo pone como primer paso, antes de cualquier skill |
| Preparación de juntas | `brief.py` corre el mismo buscador por evento y pone la prep bajo cada junta |
| El brief | Mismo buscador, misma respuesta: la prep de una junta y la consulta previa a redactar no pueden contradecirse |

Es un comando, no una intención: `scripts/consultar.py`. Una frase en una
instrucción se salta en un turno ocupado y nadie se entera. Un comando se corrió
o no se corrió.

## El orden importa

Las **reglas primero**. Son restricciones, no color. Después la gente, después
el estado de los frentes. Un draft que respeta el contexto pero rompe una regla
es peor que uno genérico: el genérico se corrige, el otro se manda.

## Cuando la wiki no sabe

Decirlo. Redactar con lo que haya y señalar el hueco. Inventar contexto que suena
plausible es la única forma de que este sistema haga daño de verdad.

## Lo que NO se construye

**Nunca un reporte semanal de aprendizaje.** El crecimiento del cerebro se ve en
`memory/changelog.md`, que se escribe solo y no le pide atención a nadie. Un
reporte es tarea que llega quiera uno o no; los que nadie lee se cobran la
confianza de todo lo que tienen alrededor.
