# replication-state.md — Build checklist and resume point

<!-- The single source of truth for build progress. Any session resuming the build:
     1. Read self-improving-os-bootstrap.md (the spec) and config/os-config.md (the parameters).
     2. Read this file to find the current phase.
     3. Never start a phase until the previous phase's acceptance test PASSED.
     Update this file in the same commit as any build step it records. -->

Last updated: 2026-09-01 by Claude (session: Phase 2 built, awaiting next-session acceptance).

## Status legend
`DONE` passed acceptance · `IN PROGRESS` being built · `BLOCKED` waiting on user/external · `PENDING` not started

## Phases

### Phase 0 — Interview → `DONE`
Interview completed 2026-08-18, answers in `config/os-config.md`. OQ-1 resolved: firewalled content sealed in tree. OQ-2 resolved: memory tree in Spanish.
- **Acceptance:** config written and confirmed by Armando. ✅

### Phase 1 — Foundation: the cache repo → `DONE`
Done 2026-08-18: local git repo initialized (branch main); full folder structure; memory tree with per-folder CLAUDE.md in Spanish; `scripts/lib/` (constants with FIREWALLED_DOMAINS in code, events, replay failing loudly on unknown kinds, codes) + `scripts/task.py` CLI; stdlib secret-scan pre-commit hook via core.hooksPath (gitleaks unavailable: no brew, and no binary downloads through the TLS-intercepted office network — swap in gitleaks later from a clean network).
- **Acceptance (local half):** ✅ test event T-1 appended → snapshot rebuilt → rendered view showed it → closed with evidence; unknown event kind rejected loudly; hook blocked a staged fake AWS key.
- **Acceptance (remote half):** ✅ 2026-09-01, on a clean network (github.com served a genuine Sectigo cert, not the FortiGate one; ports 22 and 443 both open). Account `armandoflores-oss` (personal), private repo `personal-os`, ed25519 key `SHA256:hiroBHS5sPL57QqSQZRn7CG8ye/lHaW6lGlMMTUQkII`, remote over SSH. Pushed `f63d19b`; clean clone into a temp dir diffed byte-identical against the working tree (41 files both sides); `git pull --ff-only` clean.
- **Defect found and fixed during acceptance:** `core.hooksPath` lives in `.git/config` and does NOT survive a clone — the secret-scan hook files travel, their activation does not, so a fresh clone would commit with no scanning at all, silently. Added `scripts/setup.sh` (idempotent, POSIX, verifies rather than assumes). Verified on the throwaway clone: after bootstrap the hook blocked a staged fake AWS key. **Phase 7 must assert `core.hooksPath` is set on every machine** — this is exactly a rule-10 abandoned-bot failure.
- **Account hygiene:** GitHub primary email moved to `armandofr@gmail.com` (verified); the Draiver address and its Google sign-in connection removed so the company cannot password-reset into this account. Commit identity is repo-local (`user.email=armandofr@gmail.com`), git global left with no identity.

### Phase 2 — Feedback capture: the loop's mouth → `IN PROGRESS (built, acceptance pending)`
Always-on instruction (project CLAUDE.md + skill): scan every user message for action codes, corrections, durable facts, status changes, new contacts → append events, update memory, commit, end reply with a compact receipt. Capture first, then answer.
- Built 2026-09-01: `FEEDBACK_KINDS` + `CARD_FOLDER` + firewall routing in `scripts/lib/constants.py`; `scripts/lib/feedback.py` (append-only feedback log, card writer that appends and never rewrites); `scripts/capture.py` (`mark` / `signal` / `receipt`). The always-on instruction lives at `~/.claude/CLAUDE.md` (user scope, so it loads in every session regardless of cwd); a copy is tracked here at `docs/instruccion-captura.md` — **the copy is documentation, the live file is `~/.claude/CLAUDE.md`; edit both or they drift.** Phase 7 should assert they match.
- The receipt is rendered by `capture.py receipt` from the two logs, never composed by hand, so it cannot claim a write that did not happen.
- Dry run on a throwaway copy: correction + status + contact + commitment + task create all captured from one message; a `fw-finanzas` signal was forced into `memory/privado/` and appeared in the receipt as a count only.
- **Acceptance (half 1 — same session):** ✅ a correction produces a receipt carrying the event and its lesson line.
- **Acceptance (half 2 — NEXT session):** ✅ 2026-09-02 — asked unprompted for standing draft rules and both corrections from the previous day were applied without a reminder.
- **Code scheme (2026-09-02):** `CODE_PREFIXES` T/A/P in constants; `next_code(prefix)` mints per namespace in ONE log, so codes are a display concern and merges stay trivial. Added event kinds `veto` (permanent, rule 5) and `apply_proposal`. `scripts/reply.py` parses the ten terse forms — grammar in code, and an unrecognised reply raises instead of guessing, because a misread reply writes a wrong event and that is worse than no event. All ten exercised on a throwaway clone.
- **Owed to Phase 3:** the brief renderer must print the code at the head of every replyable line, and `veto` must permanently exclude an item from ever being proposed again.

### Phase 3 — Ingest + the brief: heartbeats → `IN PROGRESS (ingest built, brief PENDING)`
Cloud ingest routine (several times/day, watermarked, single-writer on `cache/`): classify new email/calendar/transcript metadata, mint task candidates only from explicit commitments, noise gate in code, dedupe-at-creation, outbound-leg reconcile of sent messages. Daily brief at 07:00 America/Mexico_City (cron in UTC — convert, mind DST): Python renderer reading only the repo; sections per spec; every actionable line carries its T-/A-/P- code. Verify each connector with a real read before trusting it. Verify plan's runs/day allowance (~12–14 needed).
- **Ingest built 2026-09-02.** `scripts/lib/gate.py` (noise gate: meta -> exploratory -> commitment, then dedupe on action+counterparty) with 9 tests in `scripts/test_gate.py`; `scripts/ingest.py` (watermarks in `state/watermarks.json`, suppression log in `state/suppressed.ndjson`, receipts in `syncs/`, cap of 12 creates/run); outbound reconcile closes on counterparty match + >=2 distinctive title tokens.
- **Two bugs found by the dry run, both fixed:** `replay` was dropping `action`/`counterparty` from the create payload, which silently broke cross-run dedupe AND the outbound reconcile; and action extraction matched whole words, so "confirmes" and "confirmar" were different actions and the same promise could land twice.
- **The scheduler is NOT a cloud runner.** `mcp__scheduled-tasks` runs on this Mac while the app is open (missed runs fire at next launch), and its cron is LOCAL time, not UTC. Consequences: (a) the config's "cloud routine" framing is wrong for this tool; (b) the single-writer story is safe, since the laptop is the only writer; (c) an intermittently-open laptop means ingest is really catch-up-on-wake. Schedule set: `0 9,12,15,17 * * 1-5` local, plus a few minutes of scheduler jitter.
- **Verified, closing a config TODO:** America/Mexico_City has had NO DST since 2022 — UTC-6 in January and July alike. The "verify DST handling at Phase 3" note is resolved: no drift.
- **Working hours confirmed by Armando 2026-09-02: 08:30-19:00, Mon-Fri.** Schedule widened to `0 9,11,14,16,18 * * 1-5` (5 runs/day). Source: `memory/context/jornada-laboral-de-armando-08-30-19-00-cdmx.md`.
- **Documented hazard:** the 18:00 local run is 00:00 UTC the next day. Harmless while this scheduler evaluates cron in LOCAL time; if anything here ever moves to a UTC cron, that run's day-of-week must shift to `2-6` or every Friday evening run is silently skipped.
- **Hard constraint from Armando (2026-09-01): no brief item may exceed two lines.** Enforce it in the renderer — truncate or split there, never rely on a prompt to be brief. Source rule: `memory/rules/brief-maximo-dos-lineas-por-item.md`.
- **Acceptance:** three consecutive mornings of briefs needing no structural correction; replying "close <code>" works via Phase 2; no rendered item exceeds two lines.

### Phase 4 — Memory: nightly session mining → `PENDING`
Local deterministic courier (catch-up-on-wake — this laptop is intermittent): digest the day's session transcripts, scrub secret-shaped strings, exclude firewalled-folder sessions, push to `cache/sessions/<host>/`. Nightly cloud distiller: extract corrections/facts/status/contacts/commitments, dedupe, write through Phase 2 rails, delete processed digests, receipt + heartbeat, per-run cap above daily volume.
- **Acceptance:** a mid-session correction from yesterday, never explicitly saved, is applied in today's behavior and shown in the distiller receipt.

### Phase 5 — The second brain → `PENDING`
(a) Obsidian vault pointed at `memory/`, `home.md` map of content, git plugin only. (b) Density: deterministic weaver backfills `[[wikilinks]]`, topic hubs (client & deal history, people, competitive intel, pricing/tarifas per config §8), no orphans, capped links. (c) Capture lanes: paste-in-session, self-mailed links with keyword, watched folder → immutable `sources/` + distilled `context/` pages. (d) Payoff: producers consult the wiki before drafting (rule 14); `changelog.md` appended nightly. No weekly learning report ever (rule 2).
- **Acceptance:** three-hop graph navigation project→counterparty→competitor; a link self-mailed yesterday is a linked wiki page this morning; a routine draft visibly cites something never said in that session.

### Phase 6 — The loop: reconcile, grade, self-retire → `PENDING`
Nightly cloud routine after data-in, before brief: prepare (deterministic evidence gathering) → judge (model: hard closes / soft proposals / drop ambiguous) → apply (guardrails in code: id validation, firewall demotion, ~15 mutation cap, idempotency stamp, proposals ledger with 72h aging and permanent vetoes) → grade (deterministic 0-10, idempotent, distinguishes user events from system events). Weekly pass: promote recurring corrections into rules (one commit each); low-risk upgrades auto-apply, structural ones render as numbered proposals in the brief. Self-retirement at 21+ days of trend data.
- **Acceptance:** within the first week: ≥1 evidence-based close with correct receipt, zero resurfaced closed items, eval score visible in the brief.

### Phase 7 — Watchdog → `PENDING`
Manifest of every producer AND every mandatory phase within each; stdlib-only checker (always exits 0): heartbeats, named log-line assertions (amber within 24h if missing), parked state with reason/since/next-check auto-expiry, freshness from content never mtime, schedule-aware thresholds, credential-expiry countdowns. Brief banner + session-start hook only when non-green.
- **Acceptance:** stop one producer for a day → next brief says so unprompted. Delete one phase from a routine prompt → brief flags the missing capability within a day.

## Resume notes
- Repo root is this folder: `~/Documents/Claude Personal Improvement/`. Git repo on branch `main`, remote `origin` = `git@github.com:armandoflores-oss/personal-os.git` (SSH only — never HTTPS, see config §network note).
- **Next action: confirm Phase 2's second half next session** (does the capture rule hold unprompted?), then Phase 3.
- On any fresh clone, run `sh scripts/setup.sh` first — the pre-commit hook is inert until you do.
- `gitleaks` is still a stdlib stand-in; swap it in from a clean network when convenient.
- Pushing is gated by the Claude Code auto-mode classifier: Claude can commit but not push. Either Armando runs `git push` or a `Bash(git push:*)` permission rule gets added.
- Design rules in Part 2 of the spec are non-negotiable; when in doubt, re-read rule 2 (single pane), rule 8 (thin prompts, fat scripts), rule 9 (watchdog capabilities), rule 10 (abandoned-bot test).
