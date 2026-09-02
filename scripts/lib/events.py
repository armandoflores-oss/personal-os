"""Append-only event log helpers. Corrections are new events, never edits (rule 7)."""
import json
import uuid
from datetime import datetime, timezone

from . import constants


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def append_event(event: dict, log_path=None) -> dict:
    """Validate and append one event. Returns the event as written."""
    log_path = log_path or constants.TASKS_LOG
    kind = event.get("kind")
    if kind not in constants.EVENT_KINDS:
        raise ValueError(f"Unknown event kind {kind!r}; allowed: {sorted(constants.EVENT_KINDS)}")
    if "actor" not in event:
        raise ValueError("Event must carry 'actor' (e.g. 'user' or 'system:<routine>'); "
                         "the grader distinguishes user events from system events.")
    if kind == "create":
        event.setdefault("task_id", uuid.uuid4().hex[:12])
        payload = event.get("payload", {})
        domain = payload.get("domain")
        if domain not in constants.DOMAIN_SLUGS:
            raise ValueError(f"create requires payload.domain from the whitelist, got {domain!r}")
        if not payload.get("title"):
            raise ValueError("create requires payload.title")
    elif not event.get("task_id"):
        raise ValueError(f"{kind} requires task_id")
    event.setdefault("ts", _now())
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
    return event


def read_events(log_path=None):
    log_path = log_path or constants.TASKS_LOG
    events = []
    with open(log_path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"{log_path}:{n} is not valid JSON: {e}") from e
    return events
