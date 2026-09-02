#!/bin/sh
# Bootstrap a fresh clone of this repo.
#
# Why this exists: core.hooksPath lives in .git/config, which is NOT part of the
# tree and therefore does NOT survive a clone. The secret-scan hook files travel;
# their activation does not. Without this step a new machine commits with no
# secret scanning at all, silently. Run once per clone.
#
# Idempotent. Stdlib/POSIX only — no brew, no network.
set -e

root="$(git rev-parse --show-toplevel)"
cd "$root"

git config core.hooksPath scripts/hooks
chmod +x scripts/hooks/pre-commit

# Prove the hook is actually wired, not just configured.
if [ "$(git config --get core.hooksPath)" != "scripts/hooks" ]; then
    echo "FAIL: core.hooksPath did not take" >&2
    exit 1
fi
if [ ! -x scripts/hooks/pre-commit ]; then
    echo "FAIL: pre-commit is not executable" >&2
    exit 1
fi

echo "OK: hooks active (core.hooksPath=scripts/hooks)"
echo "Reminder: commit identity is repo-local. If this is a new clone, set it:"
echo "  git config user.name  \"Armando Flores\""
echo "  git config user.email \"armandofr@gmail.com\""
