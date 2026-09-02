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
}

STATUSES = {"open", "done"}
