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
    if not commit_sentences:
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


def is_duplicate(action: str, counterparty: str, open_tasks) -> str:
    """Same action + same counterparty as something already open -> suppress.
    Returns the colliding code, or ''."""
    if not action or not counterparty:
        return ""   # nothing to compare on; absence is not a match
    for t in open_tasks:
        if t.get("status") != "open" or t.get("archived"):
            continue
        if not t.get("action") or not t.get("counterparty"):
            continue   # ditto: two unknowns are not each other's duplicate
        if t["action"] == action and t["counterparty"] == counterparty:
            return t.get("code", "?")
    return ""
