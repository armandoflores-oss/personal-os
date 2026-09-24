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

## Antes de redactar cualquier cosa: consulta la wiki

**Primer paso, siempre, antes de escribir un correo, un mensaje, un deck, una
cotización, un memo o el brief.** No es opcional y no depende de si crees que
hace falta: justamente cuando crees que ya sabes el contexto es cuando se te
escapa la regla que Armando dio hace tres semanas.

```
python3 "/Users/armando/Documents/Claude Personal Improvement/scripts/consultar.py" "<persona>" "<organización>" "<tema>"
```
Para una junta: `consultar.py --evento "<título>" --asistentes correo1,correo2`

Lo que devuelve **entra en el draft**:
- Las **reglas** salen primero y son restricciones, no sugerencias. Si dicen que
  a Fede no se le manda el detalle de iteraciones internas, no se le manda.
- **Gente**: qué sabemos de cada quien y qué trae pendiente con Armando.
- **Qué está pasando**: el estado real del frente, no el que recuerdas.

Si devuelve nada, redacta con lo que tengas y **dilo**. Inventar contexto que
suena plausible es peor que admitir que la wiki no sabía.

## Vías de captura de lectura externa

Tres formas de que algo de afuera entre a la memoria. Las tres terminan igual:
**el crudo se guarda una vez en `memory/sources/` y no se vuelve a tocar**, y
una página destilada en `memory/context/` lo resume y lo enlaza.

**1. En sesión.** Si Armando pega un link o suelta un archivo y dice algo como
"ingesta esto", "guárdalo", "léelo y guárdalo": trae el contenido (WebFetch para
un link, Read para un archivo), escríbele un resumen de verdad —qué dice y por
qué le importa a él— y captúralo:
```
python3 "/Users/armando/Documents/Claude Personal Improvement/scripts/capture_source.py" add \
  --url "<url>" --texto <archivo-con-el-texto-crudo> --titulo "<título>" --resumen "<tu resumen>"
```
Para un archivo local usa `--file <ruta>` en vez de `--url`/`--texto`.
El resumen es tu trabajo; el guardado, el dedupe y el enlazado son del script.

**2. Correo a sí mismo.** Lo maneja la rutina de ingesta, no tú.

**3. Carpeta vigilada.** `~/Lecturas`. Lo que deje ahí entra en la siguiente
ingesta y el archivo se mueve a `~/Lecturas/_procesados`.

Nunca edites nada bajo `memory/sources/`: el hook lo rechaza, y con razón. Si la
lectura cambió, reescribe la página destilada.

## El brief nunca se improvisa

El brief lo renderiza `scripts/brief.py` leyendo solo el repo, y lo dispara su rutina de las 07:00.
**Nunca lo rindas conversacionalmente en una sesión como sustituto del real.** Si Armando pregunta
"¿qué tengo hoy?", responde su pregunta directamente o corre `python3 scripts/brief.py render --dry-run`
y pega la salida — pero no improvises un brief a mano. Uno redactado por ti se ve igual de bien,
se salta los tres cruces de supresión, y desde ese momento hay dos versiones de la verdad.

## Aparcar una alarma del watchdog

Si Armando dice algo como "aparca el loop hasta el lunes", "no me alarmes con el
destilador por ahora", "silencia eso un mes" — es un parqueo. Hazlo en el
momento, sin pedirle más datos de los necesarios:

```
python3 "/Users/armando/Documents/Claude Personal Improvement/scripts/watchdog.py" park <etapa> \
  --razon "<lo que él dijo, en sus términos>" --revisar <YYYY-MM-DD>
```

- El `id` de la etapa sale de `watchdog.py check`. Si no está claro cuál es,
  muéstrale las que hay y que elija; no adivines.
- **La fecha de revisión es obligatoria.** Si no la dio, elige una razonable a
  partir de lo que dijo ("hasta el lunes", "un mes") y **dile cuál pusiste**.
  Un parqueo sin fecha es olvidar algo con estilo.
- Para quitarlo: `park <etapa> --quitar`.

Aparcar **suspende** el check, no lo borra. Cuando llega la fecha, el parqueo
vence solo y la etapa vuelve a alarmar para que él lo reconsidere — aunque el
componente ya esté sano. Eso es a propósito: la decisión de aparcar también
caduca.

## Si el loop se retiró, bórralo

Al empezar cualquier sesión, si existe `state/loop/retiro.json` con la llave
`retirado`, el loop se apagó solo por no estar ganándose su lugar. Entonces,
**en esa sesión**, sin preguntar y sin ceremonia:

1. Borra la rutina con `mcp__scheduled-tasks__delete_scheduled_task`, taskId
   `loop-personal-os`.
2. Dile a Armando en una línea que se retiró, con la fecha y los tres números
   que lo decidieron.
3. No propongas revivirlo. Si lo quiere de vuelta, él lo dirá.

Armando dijo explícitamente que nunca va a agendar una revisión de esto. El
sistema que no se gana su lugar se apaga solo y se borra solo; esa es la parte
que lo hace confiable.

## Firewall

Dominios `fw-finanzas` y `fw-familia`: nunca auto-procesar, nunca cruzar con nada, nunca detallar en el recibo — solo la línea de conteo. La lista vive en `scripts/lib/constants.py`, no en este archivo.

## No frenar a Armando con aprobaciones
<!-- regla-semanal: frenar-aprobaciones -->

Armando quiere avanzar sin diálogos de por medio. Los que ve vienen de los permisos de Bash de Claude Code, no de una preferencia suya.

- No le pidas confirmación en cada cierre de tarea: son escrituras reversibles y git es el undo.
- Los comandos del Personal OS se corren **sin prefijo `cd`** (está denegado en settings) y con ruta absoluta: `python3 "/Users/armando/Documents/Claude Personal Improvement/scripts/..."`.
- Para git, `git -C "<repo>"`, nunca `cd <repo> && git`.
