"""Short display codes (T-1, T-2, ...) so Armando's replies can be terse."""
import re

from . import constants
from .events import read_events


def next_code(prefix: str = "T", log_path=None) -> str:
    """Mint the next code in one namespace. Codes are stable: once minted for an
    item they never change, and a closed item's code is never reused."""
    if prefix not in constants.CODE_PREFIXES:
        raise ValueError(f"unknown code prefix {prefix!r}; allowed: {sorted(constants.CODE_PREFIXES)}")
    highest = 0
    try:
        events = read_events(log_path or constants.TASKS_LOG)
    except FileNotFoundError:
        events = []
    for ev in events:
        if ev.get("kind") == "create":
            m = re.fullmatch(rf"{prefix}-(\d+)", ev.get("payload", {}).get("code", ""))
            if m:
                highest = max(highest, int(m.group(1)))
    return f"{prefix}-{highest + 1}"


def resolve_code(code: str, tasks: dict) -> str:
    """Map a display code to a task_id. Exact match only — codes are never guessed."""
    matches = [t for t in tasks.values() if t["code"] == code]
    if len(matches) != 1:
        raise ValueError(f"code {code!r} matches {len(matches)} tasks; expected exactly 1")
    return matches[0]["task_id"]
