#!/usr/bin/env python3
"""Block commits containing secret-shaped strings. Stdlib only.

Scans STAGED content (what would actually be committed), not the working tree.
Exit 1 on any finding; the commit aborts. False positive? Rephrase the content —
never weaken the patterns to get one commit through.
"""
import re
import subprocess
import sys

PATTERNS = [
    ("private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,}\b|\bgithub_pat_[A-Za-z0-9_]{22,}\b")),
    ("Anthropic key", re.compile(r"\bsk-ant-[A-Za-z0-9-]{20,}\b")),
    ("OpenAI-style key", re.compile(r"\bsk-[A-Za-z0-9]{32,}\b")),
    ("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("assignment of secret", re.compile(r"(?i)\b(api[_-]?key|secret|token|password|passwd|clave|contraseña)\b\s*[:=]\s*['\"][^'\"\s]{12,}['\"]")),
    ("JWT", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")),
]


def staged_files():
    out = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACM", "-z"],
                         capture_output=True, text=True, check=True).stdout
    return [f for f in out.split("\0") if f]


def staged_content(path):
    r = subprocess.run(["git", "show", f":{path}"], capture_output=True)
    try:
        return r.stdout.decode("utf-8")
    except UnicodeDecodeError:
        return None  # binary: skip content scan


def main():
    findings = []
    for path in staged_files():
        text = staged_content(path)
        if text is None:
            continue
        for n, line in enumerate(text.splitlines(), 1):
            for label, rx in PATTERNS:
                if rx.search(line):
                    findings.append(f"{path}:{n}: {label}")
    if findings:
        print("COMMIT BLOCKED — secret-shaped content staged:", file=sys.stderr)
        for f in findings:
            print(f"  {f}", file=sys.stderr)
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
