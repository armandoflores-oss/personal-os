# replication-state.md — Build checklist and resume point

<!-- The single source of truth for build progress. Any session resuming the build:
     1. Read self-improving-os-bootstrap.md (the spec) and config/os-config.md (the parameters).
     2. Read this file to find the current phase.
     3. Never start a phase until the previous phase's acceptance test PASSED.
     Update this file in the same commit as any build step it records. -->

Last updated: 2026-08-18 by Claude (session: initial build, Phase 1 local complete).

## Status legend
`DONE` passed acceptance · `IN PROGRESS` being built · `BLOCKED` waiting on user/external · `PENDING` not started

## Phases

### Phase 0 — Interview → `DONE`
Interview completed 2026-08-18, answers in `config/os-config.md`. OQ-1 resolved: firewalled content sealed in tree. OQ-2 resolved: memory tree in Spanish.
- **Acceptance:** config written and confirmed by Armando. ✅

### Phase 1 — Foundation: the cache repo → `IN PROGRESS (local DONE, remote pending)`
Done 2026-08-18: local git repo initialized (branch main); full folder structure; memory tree with per-folder CLAUDE.md in Spanish; `scripts/lib/` (constants with FIREWALLED_DOMAINS in code, events, replay failing loudly on unknown kinds, codes) + `scripts/task.py` CLI; stdlib secret-scan pre-commit hook via core.hooksPath (gitleaks unavailable: no brew, and no binary downloads through the TLS-intercepted office network — swap in gitleaks later from a clean network).
- **Acceptance (local half):** ✅ test event T-1 appended → snapshot rebuilt → rendered view showed it → closed with evidence; unknown event kind rejected loudly; hook blocked a staged fake AWS key.
- **Acceptance (remote half):** ⏳ git push/pull round-trip — pending GitHub account. Armando must create it on a CLEAN network (cellular/home, NOT office Wi-Fi — FortiGate TLS interception, see config §network note). Then: private repo, SSH deploy key, remote push.

### Phase 2 — Feedback capture: the loop's mouth → `PENDING`
Always-on instruction (project CLAUDE.md + skill): scan every user message for action codes, corrections, durable facts, status changes, new contacts → append events, update memory, commit, end reply with a compact receipt. Capture first, then answer.
- **Acceptance:** a correction said in passing produces a receipt with the event and lesson line; next session, the rule holds.

### Phase 3 — Ingest + the brief: heartbeats → `PENDING`
Cloud ingest routine (several times/day, watermarked, single-writer on `cache/`): classify new email/calendar/transcript metadata, mint task candidates only from explicit commitments, noise gate in code, dedupe-at-creation, outbound-leg reconcile of sent messages. Daily brief at 07:00 America/Mexico_City (cron in UTC — convert, mind DST): Python renderer reading only the repo; sections per spec; every actionable line carries its T-/A-/P- code. Verify each connector with a real read before trusting it. Verify plan's runs/day allowance (~12–14 needed).
- **Acceptance:** three consecutive mornings of briefs needing no structural correction; replying "close <code>" works via Phase 2.

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
- Repo root is this folder: `~/Documents/Claude Personal Improvement/`. Not yet a git repository.
- Nothing may be committed to git until OQ-1 is answered.
- Design rules in Part 2 of the spec are non-negotiable; when in doubt, re-read rule 2 (single pane), rule 8 (thin prompts, fat scripts), rule 9 (watchdog capabilities), rule 10 (abandoned-bot test).
