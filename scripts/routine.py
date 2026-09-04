#!/usr/bin/env python3
"""One entry point per routine phase, so a routine issues two fixed commands.

Why this exists: every distinct shell command a routine runs is a separate
approval the user must grant, and every time the prompt was edited the commands
changed and the previously granted approvals went stale. Armando spent an
afternoon clicking dialogs for that reason. Collapsing the work into four fixed
invocations makes the approval set small, and — more importantly — STABLE, so
approving it once is approving it for good.

  routine.py ingest-pre    heartbeat + pull + report the watermarks
  routine.py ingest-post   run all three ingest legs + commit + heartbeat
  routine.py brief-pre     heartbeat + pull
  routine.py brief-post    render + commit + heartbeat, prints the brief
"""
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"
TMP = REPO / "cache" / "tmp"


def run(args, check=False):
    r = subprocess.run(args, cwd=REPO, capture_output=True, text=True)
    if check and r.returncode != 0:
        print(f"FALLÓ: {' '.join(str(a) for a in args)}\n{r.stderr[:400]}", file=sys.stderr)
    return r


def py(script, *args, check=False):
    return run([sys.executable, str(SCRIPTS / script), *args], check=check)


def heartbeat(stage, task):
    py("heartbeat.py", stage, task)


def pull():
    r = run(["git", "-C", str(REPO), "pull", "--rebase"])
    # A failed pull is never a reason to abort: the routine's work is local and
    # the push is blocked anyway.
    return r.returncode == 0


def commit(message):
    run(["git", "-C", str(REPO), "add", "-A"])
    run(["git", "-C", str(REPO), "commit", "-m", message])


def cmd_ingest_pre():
    heartbeat("start", "ingest-personal-os")
    pull()
    TMP.mkdir(parents=True, exist_ok=True)
    marks = {}
    for src in ("gmail", "drive"):
        marks[src] = py("ingest.py", "watermark", "--source", src).stdout.strip()
    print(json.dumps({
        "watermarks": marks,
        "escribe_aqui": {
            "gmail": str(TMP / "ingest_gmail.json"),
            "drive": str(TMP / "ingest_drive.json"),
            "enviados": str(TMP / "ingest_sent.json"),
        }}, ensure_ascii=False, indent=1))


def cmd_ingest_post():
    """Runs whichever legs have a file. A connector that failed simply leaves no
    file, and the other legs still run — one dead leg never cancels the run."""
    out = []
    for src, name in (("gmail", "ingest_gmail.json"), ("drive", "ingest_drive.json")):
        f = TMP / name
        if not f.exists():
            out.append(f"{src}: sin archivo, pata omitida")
            continue
        r = py("ingest.py", "run", "--source", src, "--items", str(f), check=True)
        try:
            rec = json.loads(r.stdout)
            out.append(f"{src}: {rec['vistos']} vistos, {len(rec['creados'])} creados, "
                       f"{len(rec['suprimidos'])} suprimidos")
        except (json.JSONDecodeError, KeyError):
            out.append(f"{src}: ERROR {r.stderr[:120]}")
    sent = TMP / "ingest_sent.json"
    if sent.exists():
        r = py("ingest.py", "reconcile", "--sent", str(sent), check=True)
        try:
            rec = json.loads(r.stdout)
            out.append(f"reconciliación: {rec['revisados']} revisados, {len(rec['cerrados'])} cerrados")
        except (json.JSONDecodeError, KeyError):
            out.append(f"reconciliación: ERROR {r.stderr[:120]}")
    for f in TMP.glob("*.json"):
        f.unlink()          # los intermedios no sobreviven a la corrida
    commit("Ingesta automática")
    heartbeat("end", "ingest-personal-os")
    print("\n".join(out) if out else "nada que ingerir")


def cmd_brief_pre():
    heartbeat("start", "brief-personal-os")
    pull()
    (REPO / "cache" / "calendar").mkdir(parents=True, exist_ok=True)
    (REPO / "cache" / "transcripts").mkdir(parents=True, exist_ok=True)
    print(json.dumps({"escribe_calendario_en": str(REPO / "cache" / "calendar"),
                      "escribe_transcripciones_en": str(REPO / "cache" / "transcripts")},
                     ensure_ascii=False, indent=1))


def cmd_brief_post():
    r = py("brief.py", "render", check=True)
    print(r.stdout if r.returncode == 0 else f"brief.py FALLÓ:\n{r.stderr[:600]}")
    commit("Brief del día")
    heartbeat("end", "brief-personal-os")


CMDS = {"ingest-pre": cmd_ingest_pre, "ingest-post": cmd_ingest_post,
        "brief-pre": cmd_brief_pre, "brief-post": cmd_brief_post}


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in CMDS:
        raise SystemExit(f"uso: routine.py {{{'|'.join(CMDS)}}}")
    CMDS[sys.argv[1]]()


if __name__ == "__main__":
    main()
