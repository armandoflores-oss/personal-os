"""Shared constants. Guardrails live here, in code — never only in prompts."""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TASKS_LOG = REPO_ROOT / "tasks.ndjson"
FEEDBACK_LOG = REPO_ROOT / "feedback.ndjson"
SNAPSHOT = REPO_ROOT / "state" / "tasks-snapshot.json"
TASKS_VIEW = REPO_ROOT / "state" / "tasks-view.md"

# Display order of the brief's task sections (os-config.md §1).
DOMAINS = [
    ("cotizaciones-operativo", "Cotizaciones y pendientes operativos"),
    ("operacion-kavak", "Operación Kavak"),
    ("reuniones-espana", "Reuniones España"),
    ("grandes-deals", "Grandes deals / RFPs"),
    ("pipeline-estrategico", "Pipeline estratégico"),
    ("operacion-semanal", "Operación semanal y márgenes"),
    ("fw-finanzas", "Finanzas personales"),
    ("fw-familia", "Familia"),
]
DOMAIN_SLUGS = {slug for slug, _ in DOMAINS}

# Sealed domains (os-config.md §2): never auto-processed, never cross-referenced,
# count-only in any rendered view or receipt. Scripts MUST consult this set.
FIREWALLED_DOMAINS = {"fw-finanzas", "fw-familia"}

EVENT_KINDS = {
    "create",
    "set_status",
    "set_due_date",
    "set_owner",
    "snooze",
    "set_waiting_on",
    "set_blocked",
    "add_note",
    "archive",
    "veto",            # permanent: never propose this again (rule 5)
    "apply_proposal",  # accept a P- item now instead of waiting out its 72h
}

# Display-code namespaces (os-config.md §4). One log holds all three; the
# prefix is a display concern, so codes stay stable and merges stay trivial.
CODE_PREFIXES = {
    "T": "tarea",
    "A": "acción que te requiere",
    "P": "propuesta del sistema",
}

STATUSES = {"open", "done"}

# --- Phase 2: feedback capture -------------------------------------------
MEMORY_ROOT = REPO_ROOT / "memory"

# Signal kinds Claude may capture from a user message. Kept separate from
# EVENT_KINDS: tasks.ndjson records what happened TO a task, feedback.ndjson
# records what Armando SAID. A correction is a new event, never an edit.
FEEDBACK_KINDS = {
    "correction",   # "never do X", "that's wrong, it's Y"  -> memory/rules/
    "fact",         # "remember that Z"                     -> memory/context/
    "status",       # "closed the pilot"                    -> memory/projects/
    "contact",      # name + email together                 -> memory/people/
    "commitment",   # "I'll send it Friday"                 -> tasks.ndjson + card
    "action",       # "T-2 done", "snooze T-5 to Friday"    -> tasks.ndjson
}

# Where each kind's memory card belongs. Enforced in code so a prompt cannot
# scatter cards into the wrong folder.
CARD_FOLDER = {
    "correction": "rules",
    "fact": "context",
    "status": "projects",
    "contact": "people",
    "commitment": "projects",
}

# Firewalled signals never get a card in the normal tree and never appear in a
# receipt beyond a count. Their cards, if any, live here and nothing reads them.
FIREWALLED_CARD_FOLDER = "privado"
