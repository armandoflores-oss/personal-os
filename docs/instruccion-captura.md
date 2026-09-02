# Captura de feedback — instrucción siempre activa (Fase 2 del Personal OS)

Aplica en **toda** sesión, sin importar el directorio.
Repo: `~/Documents/Claude Personal Improvement/` · CLI: `python3 "$HOME/Documents/Claude Personal Improvement/scripts/capture.py"`

## Qué hacer en cada mensaje de Armando

Antes de responder, escanea el mensaje buscando señales durables:

| Señal | Cómo suena | `--kind` |
|---|---|---|
| Código con verbo | "T-2 listo", "cierra T-5", "pospón T-3 al viernes" | `action` |
| Corrección | "nunca hagas X", "eso está mal, es Y", "no me gusta cómo…" | `correction` |
| Hecho durable | "acuérdate que Z", "la tarifa de X es Y" | `fact` |
| Cambio de estatus | "ya cerramos el piloto", "se cayó el deal" | `status` |
| Contacto nuevo | nombre + correo juntos, o "X es la contraparte" | `contact` |
| Compromiso suyo | "te mando…", "yo hablo con…", "para el viernes" | `commitment` |

**Sin señal, no escribas nada y no pongas recibo.** El recibo nunca es decorativo.

## Cómo capturar

1. `capture.py mark` → guarda el timestamp que abre el turno.
2. Una llamada `capture.py signal` por señal. `--text` lleva **las palabras de Armando, verbatim** (es el registro de auditoría); `--lesson` lleva la línea durable que se escribe en la card. Pasa `--domain` siempre que sea evidente.
3. Para `action` y `commitment`, además el evento de tarea con `scripts/task.py`.
4. `capture.py receipt --since <ts>` → pega su salida tal cual al final de tu respuesta. **No redactes el recibo a mano:** se deriva de los logs, y esa es justamente la garantía de que no puede describir una escritura que no ocurrió.
5. Commitea lo escrito. Puedes commitear; **no puedes hacer push** (lo bloquea el clasificador) — díselo a Armando si hay algo pendiente de subir.

## Respuestas cortas de Armando (esquema de códigos)

Códigos: **T-** tarea · **A-** acción que lo requiere · **P-** propuesta del sistema. Son estables: una vez asignados no cambian, y el de un item cerrado nunca se reutiliza.

Si su mensaje empieza con un código, **no lo interpretes tú**: pásalo al parser.
`python3 scripts/reply.py parse "T-4 listo"` — y si no lo entiende, falla ruidosamente. Nunca adivines qué quiso decir; pregúntale.
`python3 scripts/reply.py forms` imprime las diez formas.

**Todo renglón que le muestres y al que pueda responder lleva su código al frente.** Sin excepción: brief, recibos, listas en conversación.

## Dos reglas duras

1. **Nunca pidas permiso para una escritura reversible.** Cards de memoria, eventos de tarea, clasificaciones: hazlas y recíbelas. Git es el undo. Pedir confirmación de lo reversible entrena a Armando a ignorar el sistema. Confirmación se reserva para: mandar cualquier cosa hacia afuera, borrar archivos, y todo lo firewalled.
2. **Nunca omitas la captura porque el mensaje también traía una pregunta.** Captura primero, responde después. La pregunta va en el cuerpo de la respuesta; el recibo va al final.

## Firewall

Dominios `fw-finanzas` y `fw-familia`: nunca auto-procesar, nunca cruzar con nada, nunca detallar en el recibo — solo la línea de conteo. La lista vive en `scripts/lib/constants.py`, no en este archivo.
