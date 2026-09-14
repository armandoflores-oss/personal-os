#!/usr/bin/env python3
"""Refuse to commit anything in this repo that names private content.

The firewall is one-way by design: a private card MAY reference a work card,
a work card NEVER names a private one. A prompt cannot enforce that — it has
to be checked mechanically, at the moment content would leave the machine.

Runs from the pre-commit hook. Reads the private vaults locally (they are on
this machine and never committed) purely to learn what names to look for.
Always exits 0 when clean; exits 1 and names the offending line otherwise.
"""
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib import constants  # noqa: E402

# Files whose job IS to describe the boundary. They may say "Privado"; they
# must still never contain a private card's name, which is checked separately.
ESTRUCTURALES = {
    ".gitignore",
    "scripts/firewall_check.py",
    "scripts/lib/constants.py",
    "scripts/hooks/pre-commit",
    "replication-state.md",
    "config/os-config.md",
}

RUTA_PRIVADA = re.compile(r"(~/Privado|/Users/[^/\s]+/Privado)")


def private_slugs():
    """Names of private cards. Learned locally; never written anywhere."""
    slugs = set()
    for vault in constants.PRIVATE_VAULTS.values():
        if not vault.exists():
            continue
        for f in vault.glob("*.md"):
            if f.stem not in ("home", "CLAUDE"):
                slugs.add(f.stem)
    return slugs


def staged_files():
    r = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
                       capture_output=True, text=True, cwd=constants.REPO_ROOT)
    return [f for f in r.stdout.splitlines() if f.strip()]


def main():
    slugs = private_slugs()
    fallas = []
    for rel in staged_files():
        path = constants.REPO_ROOT / rel
        if not path.exists() or path.suffix in (".png", ".jpg", ".pdf"):
            continue
        try:
            lines = path.read_text(errors="ignore").splitlines()
        except OSError:
            continue
        for n, line in enumerate(lines, 1):
            for s in slugs:
                if s in line:
                    fallas.append((rel, n, f"nombra una card privada: {s}"))
            if rel not in ESTRUCTURALES and RUTA_PRIVADA.search(line):
                fallas.append((rel, n, "apunta a la bóveda privada"))

    if fallas:
        print("COMMIT BLOQUEADO — el firewall es de una sola vía:", file=sys.stderr)
        for rel, n, por in fallas:
            print(f"  {rel}:{n}: {por}", file=sys.stderr)
        print("\nUna card de trabajo nunca nombra una privada. Quita la referencia;\n"
              "si de verdad hace falta el vínculo, ponlo al revés: desde la card privada.",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
