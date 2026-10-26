"""The noise gate. Deterministic, in code, never in a prompt (rule 8).

A prompt asked to "only create tasks from real commitments" drifts: it is
generous on a good day and strict on a bad one, and nothing about the drift is
visible. These rules are readable, testable, and change only by commit.

Order matters. Meta is checked before commitment because a message ABOUT a task
often quotes the commitment language of the task it discusses.
"""
import re
import unicodedata

# --- normalisation --------------------------------------------------------

def norm(text: str) -> str:
    """Lowercase, strip accents. Armando's mail is bilingual and accents are
    typed inconsistently; matching must not depend on them."""
    text = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


def sentences(text: str):
    for s in re.split(r"(?<=[.!?\n])\s+", text):
        s = s.strip()
        if s:
            yield s


# --- the three gates ------------------------------------------------------

# 1. Commentary ABOUT tasks is never itself a task.
META_MARKERS = [
    r"\bt-\d+\b", r"\ba-\d+\b", r"\bp-\d+\b",
    r"\bel brief\b", r"\bthe brief\b",
    r"\blista de pendientes\b", r"\bmis pendientes\b", r"\btask list\b",
    r"\bstatus de la tarea\b", r"\bstatus of the task\b",
    r"\bactualice? la lista\b", r"\bupdated the list\b",
    r"\brevisando pendientes\b", r"\breviewing (my |the )?tasks\b",
    r"\bcerre el ticket\b", r"\bclosed the ticket\b",
    r"\bsegun el brief\b", r"\bper the brief\b",
    r"\brecordatorio automatico\b", r"\bautomated reminder\b",
    # Notificaciones que Google genera sobre eventos. Hablan DE una junta; no
    # son un compromiso de nadie. Sin esto, cada cancelación se vuelve tarea.
    r"^\s*canceled event\b", r"^\s*cancelled event\b",
    r"^\s*invitation:", r"^\s*updated invitation:", r"^\s*invitación:",
    r"^\s*accepted:", r"^\s*declined:", r"^\s*tentatively accepted:",
    r"\bjoin with google meet\b", r"\brsvp\b",
]

# 2. A task needs somebody to have actually committed to something.
COMMITMENT_PATTERNS = [
    r"\b(te|le|les) (mando|env[ií]o|paso|comparto)\b",
    r"\bvoy a\b", r"\bvamos a\b", r"\bqued(o|amos) en\b", r"\bme comprometo\b",
    r"\bqueda pendiente que\b", r"\bnos encargamos de\b", r"\byo (hago|veo|hablo|reviso)\b",
    r"\blo (mando|env[ií]o|tengo|entrego) (el|para|antes)\b",
    r"\bi(?:'| wi)ll (send|share|get|have|deliver|prepare)\b",
    r"\bwe(?:'| wi)ll (send|share|deliver|prepare|have)\b",
    r"\bi am going to\b", r"\bwe are going to\b",
    r"\bwill (send|deliver|share) (it|the|you)\b",
    r"\bby (monday|tuesday|wednesday|thursday|friday|eod|end of day)\b",
    r"\bpara el (lunes|martes|miercoles|jueves|viernes|sabado|domingo)\b",
    r"\bantes del?\b.{0,20}\b\d{1,2}\b",
    r"\bpuedes (mandarme|enviarme|pasarme)\b", r"\bnecesito que\b",
    r"\bcan you (send|share|get) me\b", r"\bplease (send|share|confirm)\b",
]

# 2b. "Te comparto", "les envío", "adjunto" in the present tense is a DELIVERY:
#     the thing already arrived, nothing is pending. Armando (26 oct 2026): most
#     "enviar" tasks on the board were someone else's attachment. Only a future
#     marker ("te lo envío el viernes") turns the same verb back into a promise.
DELIVERY_COMMIT = COMMITMENT_PATTERNS[0]   # (te|le|les) (mando|envío|paso|comparto)
DELIVERY_PATTERNS = [
    DELIVERY_COMMIT, r"\badjunto\b", r"\b(te|le|les) anexo\b", r"\bles hago llegar\b",
    r"\b(i am|i'm|we are|we're) (sending|sharing|attaching)\b",
    r"\bplease find attached\b", r"\battached (is|are|please)\b", r"\bhere (is|are) the\b",
]
FUTURE_MARKERS = [
    r"\b(manana|pasado manana|luego|mas tarde|al rato|en un rato|en cuanto|a mas tardar)\b",
    r"\ben la (tarde|noche|manana)\b", r"\b(esta|la proxima|la siguiente) semana\b",
    r"\bel (lunes|martes|miercoles|jueves|viernes|sabado|domingo)\b",
    r"\bantes del?\b", r"\bpara el\b", r"\bcuando (tenga|tengamos|este|esten)\b",
    r"\b(tomorrow|later|next week|this week|as soon as|once (i|we))\b",
    r"\bby (monday|tuesday|wednesday|thursday|friday|eod|end of day)\b",
    r"\bon (monday|tuesday|wednesday|thursday|friday)\b",
]


def _is_delivery(sentence_norm: str) -> bool:
    """Present-tense handover with no promise left in it."""
    if not _hits(sentence_norm, DELIVERY_PATTERNS) or _hits(sentence_norm, FUTURE_MARKERS):
        return False
    # Any OTHER commitment in the same sentence ("adjunto X y voy a revisar Y")
    # is still a commitment.
    return set(_hits(sentence_norm, COMMITMENT_PATTERNS)) <= {DELIVERY_COMMIT}


# 3. Hedged language never becomes a task ON ITS OWN.
EXPLORATORY_MARKERS = [
    r"\btal vez\b", r"\bquiza\b", r"\bquizas\b", r"\ba lo mejor\b",
    r"\bpodriamos\b", r"\bpodria\b", r"\bhabria que ver\b", r"\bestaria bien\b",
    r"\bdeberiamos considerar\b", r"\bvaldria la pena\b", r"\bque tal si\b",
    r"\by si\b", r"\bpensando en\b", r"\bexplorando\b", r"\bidea suelta\b",
    r"\bmaybe\b", r"\bperhaps\b", r"\bwe could\b", r"\bwe might\b",
    r"\bwhat if\b", r"\bworth considering\b", r"\bjust thinking\b",
    r"\bnice to have\b", r"\bat some point\b", r"\beventually\b",
    r"\bexploring\b", r"\bbrainstorm\b",
]

# 4. A client or prospect asking Armando something is a task even when nobody
#    wrote a promise. Without this gate the Borusan thread was suppressed three
#    times as sin_compromiso (sep 2026) and the drop in created tasks from
#    week 40 on came from the same hole: a client's question is not a
#    commitment, so only Draiver's own promises ever became tasks.
#    Rules it honours (memory/rules/correo-pendiente-*.md): it only counts if
#    it asks Armando, not the team.
OWN_DOMAINS = ("driverdo.com", "draiver.com")
GENERIC_DOMAINS = ("gmail.com", "hotmail.com", "outlook.com", "live.com", "live.com.mx",
                   "yahoo.com", "yahoo.com.mx", "icloud.com")
AUTOMATED_SENDER = re.compile(
    r"^(no-?reply|do-?not-?reply|notifica\w*|notification\w*|alerts?|news\w*|"
    r"marketing|mailer\w*|bounce\w*|info|hello|support|soporte|calendar\w*|"
    r"drive-shares\w*|billing|receipts?|team)\b")
AUTOMATED_SUBJECT = [r"\brecibo\b", r"\breceipt\b", r"\bpayment confirmation\b",
                     r"\bpedido\b", r"\border\b", r"\bnewsletter\b", r"\bunsubscribe\b",
                     r"\bwebinar\b", r"\bnotes by gemini\b"]
REQUEST_PATTERNS = [
    r"\b(nos|me) (puedes|podrias|pueden|podrian|ayudas|ayudarias)\b",
    r"\bpodrias\b", r"\bpodrian\b", r"\bfavor de\b", r"\bte pido\b", r"\ble pido\b",
    r"\bagradecere\w*\b", r"\bagradeceria\w*\b", r"\bsolicit(o|amos)\b",
    r"\b(necesitamos|requerimos) (que|tu|su|de)\b",
    r"\b(quedo|quedamos) (atent[oa]s?|pendientes?) (a|de) (tu|su|vuestra) "
    r"(respuesta|propuesta|confirmacion|comentarios|cotizacion|retroalimentacion)\b",
    r"\ben espera de (tu|su|vuestra)\b",
    r"\b(esperamos|espero) (tu|su|vuestra) (respuesta|propuesta|confirmacion|comentarios|cotizacion)\b",
    r"\b(could|can|would) you\b", r"\blet (me|us) know\b", r"\bplease (send|share|confirm|advise|review|let)\b",
    r"\blooking forward to (your|hearing)\b", r"\bawaiting your\b", r"\bwe need your\b",
]
GREETING_QUESTION = re.compile(r"\b(como (estas|estan|esta|te va|les va)|how are you|que tal)\b")


def _external_sender(sender: str) -> bool:
    if "@" not in sender:
        return False
    local, dom = sender.lower().split("@", 1)
    return (dom not in OWN_DOMAINS and dom not in GENERIC_DOMAINS
            and not AUTOMATED_SENDER.match(local))


def _asks_armando(item: dict, text: str) -> bool:
    """The ask is his if he is a recipient AND either the only Draiver one or
    named in the opening of the body. A question to a team list is the team's."""
    recips = [r.lower() for r in item.get("recipients") or []]
    if not any("armando" in r.split("@")[0] for r in recips):
        return False
    internal = [r for r in recips if r.split("@")[-1] in OWN_DOMAINS]
    return len(internal) <= 1 or "armando" in norm(item.get("text", ""))[:300]


def client_request(item: dict):
    """The sentence where an outside party asks Armando for something, or None."""
    if not _external_sender(item.get("sender", "")):
        return None
    if _hits(norm(item.get("subject", "")), AUTOMATED_SUBJECT):
        return None
    if not _asks_armando(item, item.get("text", "")):
        return None
    for s in sentences(item.get("text", "")):
        n = norm(s)
        if _hits(n, EXPLORATORY_MARKERS):
            continue   # a floated idea stays a floated idea, even from a client
        if _hits(n, REQUEST_PATTERNS):
            return s
        if "?" in s and len(s.split()) >= 4 and not GREETING_QUESTION.search(n):
            return s
    return None


CLIENTS = ["kavak", "clicars", "uber", "element", "tesla", "ford", "cemex",
           "vemo", "tip", "draiver", "driverdo"]

DOMAIN_KEYWORDS = {
    "operacion-kavak": ["kavak"],
    "reuniones-espana": ["clicars", "espana", "madrid", "barcelona", "spain launch"],
    "grandes-deals": ["rfp", "uber av", "field support", "optimizador de flota",
                      "fleet optimizer", "licitacion", "propuesta comercial"],
    "pipeline-estrategico": ["ford", "tesla", "element", "automatizacion",
                             "automation", "flujo de viajes", "trip flow"],
    "operacion-semanal": ["margen", "margin", "weekly", "semanal", "townhall",
                          "junta de comunicacion", "board", "all-hands"],
    "cotizaciones-operativo": ["cotiza", "quote", "tarifa",
                               "cemex", "vemo", "tip ", "traslado"],
}
DEFAULT_DOMAIN = "cotizaciones-operativo"

# Tie-break. A named account beats the catch-all bucket: "cotización de Kavak"
# is Kavak work that happens to be a quote, not generic quoting.
SPECIFICITY = {
    "operacion-kavak": 3, "reuniones-espana": 3, "grandes-deals": 2,
    "pipeline-estrategico": 2, "operacion-semanal": 1, "cotizaciones-operativo": 0,
}

# Stems, not full forms: dedupe compares actions, so "confirmes", "confirmar"
# and "confirmo" must collapse to one action or the same promise slips through
# twice under different conjugations.
ACTION_STEMS = {
    "enviar": ["mand", "envi", "pas", "compart", "send", "shar", "deliver"],
    "revisar": ["revis", "chec", "review"],
    "cotizar": ["cotiz", "quot", "pricing"],
    "confirmar": ["confirm"],
    "agendar": ["agend", "schedul", "book"],
    "preparar": ["prepar", "arm", "draft"],
}


def _hits(text, patterns):
    return [p for p in patterns if re.search(p, text)]


def classify_domain(text: str, sender: str = "") -> str:
    t = norm(f"{text} {sender}")
    best, best_n = DEFAULT_DOMAIN, 0
    for slug, kws in DOMAIN_KEYWORDS.items():
        n = sum(1 for k in kws if k in t)
        if n > best_n or (n == best_n and n > 0
                          and SPECIFICITY[slug] > SPECIFICITY[best]):
            best, best_n = slug, n
    return best


def extract_action(text: str) -> str:
    t = norm(text)
    for canonical, stems in ACTION_STEMS.items():
        if any(re.search(rf"\b{st}\w*", t) for st in stems):
            return canonical
    return "otro"


def extract_counterparty(text: str, sender: str = "", recipients=None) -> str:
    """Who the commitment is with. Named client wins; otherwise the other
    party's mail domain; otherwise the sender's local part."""
    t = norm(f"{text} {sender} {' '.join(recipients or [])}")
    for c in CLIENTS:
        if c in ("draiver", "driverdo"):
            continue
        if c in t:
            return c
    if sender.startswith("gemini-notes"):
        return "interno"   # el anotador de juntas no es contraparte de nada
    for addr in list(recipients or []) + [sender]:
        if "@" in addr:
            dom = addr.split("@", 1)[1].lower()
            if dom not in ("driverdo.com", "draiver.com"):
                return dom.split(".")[0]
    return (sender.split("@")[0].lower() if sender else "interno")


def evaluate(item: dict) -> dict:
    """Decide whether one ingested item may become a task candidate.

    Returns {"accept": bool, "reason": str, ...}. `reason` is always populated,
    including on accept, because every suppression must be explainable later.
    """
    text = f"{item.get('subject','')}\n{item.get('text','')}"
    t = norm(text)

    meta = _hits(t, META_MARKERS)
    if meta:
        return {"accept": False, "reason": "meta", "detail": meta[0]}

    commit_sentences = [s for s in sentences(text) if _hits(norm(s), COMMITMENT_PATTERNS)]
    delivered = [s for s in commit_sentences if _is_delivery(norm(s))]
    commit_sentences = [s for s in commit_sentences if s not in delivered]
    if not commit_sentences:
        ask = client_request(item)
        if ask:
            action = extract_action(ask)
            return {
                "accept": True,
                "reason": "cliente_espera_respuesta",
                "sentence": ask[:200],
                "action": action if action != "otro" else "responder",
                "counterparty": extract_counterparty(text, item.get("sender", ""), item.get("recipients")),
                "domain": classify_domain(text, item.get("sender", "")),
            }
        if delivered:
            return {"accept": False, "reason": "entregado", "detail": delivered[0][:120]}
        # Distinguish "nothing was promised" from "something was floated".
        hedges = _hits(t, EXPLORATORY_MARKERS)
        if hedges:
            return {"accept": False, "reason": "exploratorio", "detail": hedges[0]}
        return {"accept": False, "reason": "sin_compromiso", "detail": ""}

    # Exploratory kills only the sentences it appears in. If every committing
    # sentence is hedged, the whole item is exploratory.
    firm = [s for s in commit_sentences if not _hits(norm(s), EXPLORATORY_MARKERS)]
    if not firm:
        return {"accept": False, "reason": "exploratorio",
                "detail": _hits(norm(commit_sentences[0]), EXPLORATORY_MARKERS)[0]}

    return {
        "accept": True,
        "reason": "compromiso_explicito",
        "sentence": firm[0][:200],
        "action": extract_action(firm[0]),
        "counterparty": extract_counterparty(text, item.get("sender", ""), item.get("recipients")),
        "domain": classify_domain(text, item.get("sender", "")),
    }


VERBS = {"enviar": "Enviar", "confirmar": "Confirmar", "cotizar": "Cotizar",
         "agendar": "Agendar", "revisar": "Revisar", "preparar": "Preparar",
         "responder": "Responder"}
REPLY_PREFIX = re.compile(r"^\s*((re|rv|fw|fwd|r)\s*:\s*)+", re.I)


def _who(counterparty: str) -> str:
    if not counterparty or counterparty == "interno":
        return "el equipo"
    # Una parte local de correo (diego.diaz) es una persona; lo demás, una marca.
    if "." in counterparty:
        return " ".join(w.capitalize() for w in counterparty.split("."))
    return counterparty.capitalize()


def task_title(verdict: dict, item: dict) -> str:
    """Qué hay que hacer y con quién, no el asunto del correo. El asunto queda
    al final, limpio de Re:/RV:, porque es lo que se busca en el buzón.

    Si el compromiso es de Armando o un cliente le pide algo, el verbo es suyo.
    Si el que prometió fue otro, a Armando le toca darle seguimiento."""
    subject = REPLY_PREFIX.sub("", item.get("subject") or "").strip()
    who = _who(verdict.get("counterparty", ""))
    mine = "armando" in (item.get("sender") or "").lower().split("@")[0]
    if verdict.get("reason") == "cliente_espera_respuesta" or mine:
        lead = f"{VERBS.get(verdict.get('action'), 'Responder')} a {who}"
    else:
        lead = f"Seguimiento con {who}"
    return f"{lead}: {subject}"[:120] if subject else lead


def is_duplicate(action: str, counterparty: str, open_tasks, subject: str = "") -> str:
    """Same action + same counterparty as something already open -> suppress.
    Also the same thread with the same counterparty, whatever the action: T-34
    and T-77 were one REPSE thread split by "confirm" vs "send".
    Returns the colliding code, or ''."""
    if not action or not counterparty:
        return ""   # nothing to compare on; absence is not a match
    thread = norm(REPLY_PREFIX.sub("", subject).strip())
    for t in open_tasks:
        if t.get("status") != "open" or t.get("archived"):
            continue
        if (len(thread) > 8 and t.get("counterparty") == counterparty
                and thread in norm(t.get("title") or "")):
            return t.get("code", "?")
        if not t.get("action") or not t.get("counterparty"):
            continue   # ditto: two unknowns are not each other's duplicate
        if t["action"] == action and t["counterparty"] == counterparty:
            return t.get("code", "?")
    return ""
