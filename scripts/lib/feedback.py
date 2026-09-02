"""Phase 2 rails: append feedback events and update memory cards.

Two invariants this module exists to enforce, in code rather than in a prompt:
  1. feedback.ndjson is append-only. A correction of a correction is a new
     event; nothing is ever edited or removed (rule 7).
  2. Firewalled domains never get a card in the browsable tree and never appear
     in a receipt beyond a count (rule 6).
"""
import json
import re
import uuid
from datetime import datetime, timezone

from . import constants


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def slugify(text: str) -> str:
    text = text.lower().strip()
    for a, b in (("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"), ("ñ", "n")):
        text = text.replace(a, b)
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text[:60] or "sin-titulo"


def append_feedback(kind: str, text: str, *, actor: str = "user", lesson: str = None,
                    card: str = None, domain: str = None, code: str = None,
                    log_path=None) -> dict:
    """Validate and append one feedback event. Returns the event as written."""
    if kind not in constants.FEEDBACK_KINDS:
        raise ValueError(f"Unknown feedback kind {kind!r}; allowed: {sorted(constants.FEEDBACK_KINDS)}")
    if not text or not text.strip():
        raise ValueError("feedback requires the user's own words in --text (verbatim, for audit)")
    if domain is not None and domain not in constants.DOMAIN_SLUGS:
        raise ValueError(f"unknown domain {domain!r}")
    event = {
        "id": uuid.uuid4().hex[:12],
        "ts": _now(),
        "actor": actor,
        "kind": kind,
        "text": text.strip(),
        "lesson": (lesson or "").strip() or None,
        "card": card,
        "domain": domain,
        "code": code,
        "firewalled": domain in constants.FIREWALLED_DOMAINS if domain else False,
    }
    path = log_path or constants.FEEDBACK_LOG
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
    return event


def card_path(kind: str, title: str, domain: str = None) -> str:
    """Decide where a card lives. Firewalled domains are forced into privado/."""
    if domain and domain in constants.FIREWALLED_DOMAINS:
        folder = constants.FIREWALLED_CARD_FOLDER
    else:
        folder = constants.CARD_FOLDER.get(kind)
        if folder is None:
            raise ValueError(f"kind {kind!r} does not get a card")
    return f"memory/{folder}/{slugify(title)}.md"


def write_card(rel_path: str, title: str, line: str, *, source: str) -> tuple[str, bool]:
    """Append one dated line to a card, creating it with frontmatter if new.

    Cards accumulate; they are never rewritten. Returns (rel_path, created).
    """
    path = constants.REPO_ROOT / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    created = not path.exists()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if created:
        header = (
            f"---\ntitulo: {title}\ncreada: {today}\n---\n\n"
            f"# {title}\n\n"
        )
        path.write_text(header, encoding="utf-8")
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"- {today} — {line}  <!-- {source} -->\n")
    return rel_path, created


def read_feedback(log_path=None):
    path = log_path or constants.FEEDBACK_LOG
    events = []
    if not path.exists():
        return events
    with open(path, encoding="utf-8") as f:
        for n, raw in enumerate(f, 1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                events.append(json.loads(raw))
            except json.JSONDecodeError as e:
                raise ValueError(f"{path}:{n} is not valid JSON: {e}") from e
    return events
