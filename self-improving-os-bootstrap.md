# Self-Improving Personal OS — Bootstrap Guide for Claude Code

*Version 2.0, 30 July 2026. Changes since v1.0 (9 July): the second brain is now a build phase of its own (Part 4, Phase 5), the memory tree has a taxonomy rule, the watchdog watches capabilities rather than only outputs, and retrieval-before-production is a design rule. Phases 5 and 6 of v1.0 are now 6 and 7.*

**How to use this file (for the human):** put it in an empty folder, open Claude Code there, and say: *"Read self-improving-os-bootstrap.md and build my OS."* Claude will interview you first, then build the system in phases across several sessions. You need: Claude Code, a private GitHub repository (Claude will help you create it), Obsidian (free, arrives at Phase 5), and ideally a Claude plan that supports scheduled cloud routines. Nothing here contains anyone else's data; your system starts empty and learns only from you.

**What you get:** a personal operating system where one daily brief is the only thing you read, everything you say in passing becomes durable memory, tasks close themselves when there is evidence the work happened, the knowledge you accumulate is browsable and actually improves your first drafts, the system grades its own output nightly, and any automation that stops earning its keep retires itself. The foundation lands in one session; the full loop after a stretch of normal use.

---

## PART 1 — FOR CLAUDE: WHAT YOU ARE BUILDING

You (Claude Code) are the builder and, later, the operator of a personal OS for a busy executive. The architecture has five boxes; everything else is plumbing:

| Box | Concrete form |
|---|---|
| **Runtime** | Claude Code sessions + one private git repository (the "cache repo") that laptop, cloud routines, and any other machine all read and write through git |
| **Heartbeats** | Scheduled routines: data ingest several times a day, a morning brief, a nightly memory distiller, a nightly reconcile-and-grade loop, a watchdog over all of them |
| **Memory** | Two layers. Below: append-only event logs (tasks, feedback) and immutable captured sources. Above: a cross-linked wiki of markdown cards (people, projects, topics, system, interactions, glossary, lessons) that the nightly routines maintain and the user browses in Obsidian |
| **Evals** | A nightly mechanical grader that scores the system's own output and logs a trend |
| **Self-improvement loop** | Capture corrections → distill sessions → reconcile task state from evidence → grade → promote recurring lessons into rules → propose or apply its own upgrades → retire itself if it stops helping |

The user's total obligation: read one brief per day and reply in natural one-line messages. Everything else is the system's job.

## PART 2 — NON-NEGOTIABLE DESIGN RULES

These rules are the transferable core. Each one was paid for with a real failure in a production system of this kind. Do not trade them away for convenience.

1. **Interview before building.** You know nothing about this user's projects, priorities, or confidentiality needs. Phase 0 exists to learn them. Never assume, never copy examples from this guide into their system as if they were data.
2. **Single pane.** Exactly ONE surface the user reads: the daily brief. Every receipt, proposal, alert, and score lands there. Never create a second channel, a review folder, a dashboard, or a notification stream. Systems that add surfaces get ignored, then resented, then killed. **Corollary once Phase 5 exists:** the wiki is a library, never a queue. Nothing in it ever waits for the user, nothing in it is homework, and it does not become surface number two. Evidence from a comparable system: 81 consecutive daily briefs with a checkbox interface, zero checkboxes ever ticked.
3. **Reply, not click.** All user interaction is conversational: "A3 done", "snooze T-12 to Friday", "that contact is wrong". No checkboxes, no buttons, no forms. Conversational feedback in the same system produced hundreds of events over the period the checkboxes produced zero.
4. **Apply now, receipt always, git is the undo.** For reversible changes (memory writes, task events, classifications) act without asking, show a compact receipt at the end of the reply or in the brief, and rely on git history for rollback. Asking for confirmation on reversible things trains the user to ignore the system. Confirmation is reserved for: sending anything external (email, messages), deleting files, and anything in a firewalled domain.
5. **Silence is consent, with aging.** Hard evidence acts immediately. Soft evidence becomes a proposal that appears in the brief with its close date; untouched for 72h, it applies. One veto and that item is never proposed again. This converts review queues from homework into headlines. Queues that wait for explicit approval rot: measured in a comparable system, a pending-review file went untouched for weeks until an audit found it.
6. **Firewalls first.** In the interview, the user declares domains that are confidential or sensitive (typically: personal finance, health, family, legal matters, compensation). Those domains: never auto-close, never auto-process, never appear in receipts except as count-only lines ("2 items withheld"), never leave their folder. Encode the list in code (a constant in the scripts), not just in prompts. Once Phase 5 exists, firewalled knowledge lives in physically separate vaults outside the cloud-synced repo, and linking is one-way: a private card may reference a work card, a work card never names a private one.
7. **Event logs are the truth.** Tasks and feedback live in append-only `.ndjson` logs. Corrections are new events, never edits. Every snapshot (current task state, feedback overlay) is derived and rebuildable from the logs. When two machines conflict, the logs merge trivially and the snapshots rebuild. Display views (the rendered task list) are generated files nobody edits by hand.
8. **Thin prompts, fat scripts.** Scheduled-routine prompts beyond roughly 300 lines fail silently on cloud platforms. All mechanics (parsing, matching, caps, validation, file writes) live in small Python scripts in the repo; the routine's model only does judgment (is this evidence sufficient? are these two tasks the same action?) between script calls. Guardrails live IN the scripts, never only in the prompt: firewall demotion, mutation caps, id validation, idempotency stamps.
9. **Watchdog the capabilities, not only the outputs.** Silent failure is the default failure mode of scheduled automation, and it has three distinct shapes. (a) A producer stops producing: every producer writes a heartbeat, a manifest-driven health check evaluates all of them, and the brief carries a banner when something is stale. (b) A capability loses its caller: in a comparable system a reconciler built precisely to auto-close tasks lost its invocation during a routine rebuild and ran zero times for three weeks, discovered only by accident. Therefore every mandatory phase asserts its own named log line, the health check alarms on a missing assertion within 24h, and any routine rebuild diffs its phase inventory against the architecture doc before deploy. (c) A known outage becomes permanent noise: give the health check a **parked** state carrying a reason, a since-date and a next-check date that auto-expires, so a diagnosed third-party breakage stops re-alarming as if it were fresh. Success log lines must assert the outcome invariant (file exists, push landed) rather than narrate intent ("finished"). Beware: file modification times lie in freshly cloned repos and after merges; derive freshness from content (dates in filenames or JSON fields), never from mtime.
10. **The abandoned-bot test (apply to every new automation, including the ones in this guide).** Before building anything new ask: (a) does it only SUBTRACT from surfaces the user already reads, never add one they must tend? (b) does it carry zero scheduled evaluation burden for the user (never "let's review it in N weeks")? (c) does it ship with self-retirement: it measures itself against its own baseline, proposes its own shutdown in the brief when it stops paying, and silence executes the retirement? If any answer is no, redesign or don't build.
11. **Wrong closes are cheaper than lost trust only if they are visible.** Every automatic action appears in the brief with its evidence and a one-line reopen affordance. The user skimming past receipts is fine; the user discovering an invisible action is fatal.
12. **Names and addresses are never guessed.** Any person, company, email address, or figure the system uses must trace to the user's own glossary or an explicit message. A hallucinated email address sent to a real thread is the canonical disaster; make the glossary the mandatory lookup before any send.
13. **One folder, one question.** Every memory folder answers exactly one question, and the test for any new card is which question it answers. `people/` who is this person; `topics/` what is this organization or theme and who belongs to it; `projects/` what am I driving and to what end state; `system/` what maintains this brain; `interactions/` what happened, dated; `sources/` plus the wiki what did I capture and what did it distil into. Two hard consequences: **a dated artifact is not memory** (one meeting's notes belong in a meetings folder, never in the tree), and **one entity, one card** (new facts go onto the existing node, never into a second card in a different folder). Skipping this rule is why memory trees stop being browsable at around eighty files: the same company appears in three places and the user declares the whole thing messy.
14. **Retrieval before production.** Accumulated knowledge that nothing reads is a landfill, not a brain. Every recurring producer (the brief renderer, meeting prep, any drafting skill) carries a standing first step: consult the wiki for the entities and topics involved before drafting. Without this rule the memory grows, the graph looks impressive, and not a single first draft gets better. It is the difference between a system that stores and a system that compounds.
15. **No orphans.** Every card must be reachable in the graph: linked from at least one project card, topic hub, or the home page. Whoever creates a card links it from its hub in the same commit. Cap links per card so topic hubs carry the density and entity cards stay tight; a graph where everything links everything is as unreadable as no graph at all.

## PART 3 — PHASE 0: THE INTERVIEW

Before creating any file, interview the user. Use your question tool if available; batch related questions; keep it under 15 minutes. Capture:

1. **Domains and priority.** "List the projects or areas you want this system to track, in priority order." Also: which single domain, if any, outranks everything (their existential priority). Use THEIR names for domains; never suggest examples from anyone else's life.
2. **Firewalled domains.** "Which topics must this system treat as sealed: visible to you only, never auto-processed, never cross-referenced?" (Prompt them to consider: personal finance, health, family, legal, compensation.) Ask a second question here: which of those deserve a physically separate vault at Phase 5, and which are fine as a tagged-but-sealed domain inside the main tree.
3. **The one surface.** When do they want the daily brief (their local time), and in which language? Any register rules (formal/informal, dialect preferences, banned phrasings)? Encode language rules as always-on instructions, because model dialect drift is real and recurring. Consider defaulting the memory tree itself to a single language regardless of the brief's language: it removes an entire class of drift.
4. **Feedback style.** Confirm the covenant: they reply in one-liners, the system does the rest. Agree the code scheme (T-codes for tasks, A-codes for actions) so their replies can be terse.
5. **Data sources.** Which connectors exist or can be enabled: email, calendar, document storage, meeting transcription, team messaging. Which accounts are work vs personal (this affects firewalls). Note: a connector showing "connected" is not proof it is connected to the RIGHT account with the right read scope; verify empirically with a real read before trusting it.
6. **Infrastructure and plan.** Do they have: a Claude plan that supports scheduled cloud routines (preferred for all LLM steps), and how many runs per day does it allow? A GitHub account? An always-on machine (optional; useful only for deterministic collectors)? If their seat cannot schedule cloud routines, say so now and design the degraded mode in Part 6 rather than discovering it at Phase 3. IMPORTANT platform trap: on Windows, headless or scheduled invocation of Claude Code generally cannot authenticate even when the interactive terminal is logged in. Never design local automation that needs headless Claude; LLM steps go to cloud routines, local scheduled tasks run only deterministic scripts.
7. **Autonomy appetite.** Default recommendation (start here, widen later): hard evidence acts automatically with receipts; soft evidence proposes with 72h silence-consent; firewalled domains propose-only forever; external sends always confirmed.
8. **What they read.** For Phase 5: what sources of outside knowledge do they want captured (articles, newsletters, links colleagues send, documents)? And what would they want to ask their own brain in six months? Their answer shapes the topic hubs.

Write the answers to `config/os-config.md` in the repo. Every later phase parameterizes from this file. Then create `replication-state.md` (a checklist of the phases below) and keep it updated so any future session can resume the build.

## PART 4 — BUILD PHASES

Build in this order. Each phase ends with an acceptance test the user can see. Do not start a phase until the previous one's test passes.

### Phase 1 — Foundation: the cache repo
Create a PRIVATE GitHub repository. Structure:
```
cache/          incoming metadata (email/calendar/transcript records as JSON)
enriched/       full-content extracts where needed (respect firewall rules)
briefs/         rendered daily briefs (derived, never hand-edited)
state/          derived snapshots (rebuildable), health, watermarks
scripts/        all Python logic (stdlib-only where possible)
config/         os-config.md, contacts, classification rules, routine prompts
memory/         the wiki. See the taxonomy below; rule 13 governs what goes where
syncs/          receipts from every scheduled run
tasks.ndjson    append-only task event log
feedback.ndjson append-only feedback event log
```
The `memory/` tree, per rule 13, one folder one question:
```
memory/home.md              entry point, map of content
memory/glossary.md          name/alias/email tuples, acronyms, terms. Lookup only, no biography
memory/people/<slug>.md     who is this person
memory/topics/<slug>.md     organization or theme hubs, and who belongs to them
memory/projects/<slug>.md   what the user is driving, and to what end state
memory/system/<slug>.md     what maintains this brain (the automations themselves)
memory/interactions/<slug>-interactions.md   dated ledgers, loaded on demand only
memory/sources/<slug>.md    captured external material, immutable (Phase 5)
memory/context/<slug>.md    distilled wiki pages written from sources (Phase 5)
memory/rules/               durable "how I want things done" rules
```
Every folder gets a short CLAUDE.md: purpose, audience, confidentiality tier, language, and the one question it answers. Install a secret-scanning pre-commit hook (e.g. gitleaks) day one. Write `scripts/lib/` with: event append helpers, snapshot rebuild (replay the log), a task-code generator (short display codes), and a task-state replayer that fails loudly on unknown event kinds. Event kinds to support: create, set_status, set_due_date, set_owner, snooze, set_waiting_on, set_blocked, add_note, archive.
**Acceptance:** append a test event → rebuild snapshot → rendered task list shows it; git push/pull round-trips.

### Phase 2 — Feedback capture: the loop's mouth
An always-on instruction (project CLAUDE.md + a skill if supported): scan EVERY user message for signals: action codes with verbs ("A1 done"), corrections ("never do X", "that's wrong, it's Y"), durable facts ("remember that Z"), project status ("closed the pilot"), new contacts (name + email together). On any hit: append the matching event(s), update the relevant memory card or glossary line, commit, and end the reply with a compact receipt (one line per file touched). Never skip capture because the message also contained a question: capture first, then answer.
**Acceptance:** the user says a correction in passing; the receipt shows the event and the lesson line; next session, the rule holds.

### Phase 3 — Ingest + the brief: heartbeats
**Ingest** (cloud routine, several times a day within the user's working hours): pull NEW email/calendar/transcript metadata since the last watermark into `cache/` as one JSON per item, classify each (domain tag from a closed whitelist, urgency, is-the-user-awaited), and mint task candidates ONLY from explicit commitments. Noise gate in code: junk patterns blocked, exploratory verbs ("evaluate", "explore") never become tasks directly, no meta-tasks (an item whose content is commentary about tasks), dedupe-at-creation against open tasks (same action + same counterparty = suppress, log to a skip file). Include an outbound leg: reconcile the user's own sent messages against open tasks, because a task whose proof-of-done is a message the user sends will otherwise stay open until the counterpart happens to reply. Single-writer rule: only ingest writes `cache/` and watermarks.
**The brief** (cloud routine, daily at the user's chosen time): a Python renderer, not a prompt, reading only the repo. Sections: health banner (only when something is stale or parked); today's calendar with prep notes; open tasks by the user's priority order with display codes and due dates; new actions requiring the user (each cross-checked: suppressed if a task already covers it, if a recent meeting covered it, or if feedback marked it closed); receipts of everything the system did overnight (auto-closes with evidence, proposals with their close dates, yesterday's self-grade); noise, count-only. Every line the user might respond to carries its code.
**Traps:** cloud cron fields are usually UTC, convert from the user's timezone; test the routine by firing it once manually and reading its receipt; never render the brief conversationally in-session as a substitute for the pipeline (hand-rendered briefs drift and skip the enforcement checks).
**Acceptance:** three consecutive mornings of briefs that the user did not have to correct on structure; replying "close <code>" works via Phase 2.

### Phase 4 — Memory: nightly session mining
Verbal feedback captured live (Phase 2) misses things said mid-work. Add: a device courier (local scheduled script, deterministic, no LLM) that each evening digests the day's Claude Code session transcripts into compact text digests (user messages verbatim, assistant messages truncated), scrubs secret-shaped strings, EXCLUDES sessions from firewalled folders, and pushes them to `cache/sessions/<host>/`. A nightly cloud routine (the distiller) reads the digests and extracts: corrections, durable facts, project status changes, new contacts, commitments; dedupes against existing memory; writes through the same rails as Phase 2; deletes processed digests; writes a receipt and a heartbeat. Size the per-run cap ABOVE daily session volume and state the remaining queue in the receipt when capped. Filter out digest noise at the courier (sessions with zero user messages, e.g. failed scheduled jobs) so the queue metric stays honest.
**Acceptance:** a correction made mid-session yesterday, never explicitly "saved", appears applied in today's behavior and in the distiller receipt.

### Phase 5 — The second brain: make the memory browsable, then make it useful
Everything so far writes memory that nobody can see. This phase gives it a shape, a window, and a job. The pattern is Karpathy's LLM wiki: **the wiki is the codebase, the LLM is the programmer, Obsidian is only the IDE.** Claude does all maintenance; the user never files anything.

Four parts, in order:

**(a) The window.** An Obsidian vault is nothing but a folder of markdown files that the app opens, so point it at `memory/` and the vault exists. No migration, no new store, no new sync system: the repo already travels between machines. Build `home.md` as the map of content. Install only the git plugin so the vault refreshes when the user opens it; resist the plugin zoo. If the user has firewalled domains that earned a separate vault in interview question 2, create those trees OUTSIDE the synced repo, and enforce the one-way linking rule from design rule 6. Separate vault files mean the app physically cannot draw work and private content in one graph.

**(b) Density.** Cards that do not link to each other are silos. Backfill `[[wikilinks]]` across the existing tree with a deterministic weaver script (idempotent, never auto-links bare first names, respects a per-card allowlist where a domain is sensitive). Create topic hubs for the organizations and themes that recur, and enforce rule 15: no orphans, links capped per card. Extend the memory schema file with the linking contract so every future automated write maintains the web instead of eroding it.

**(c) Capture.** Nothing yet records what the user READS. Give them capture lanes ranked by effort: paste a link or file into any session and one command ingests it; mail the link to themselves with a keyword in the subject so the existing collector picks it up; drop files into a watched folder. Each ingestion writes the raw material to `sources/` and NEVER edits it again, then writes or updates a distilled wiki page in `context/` linked to the relevant people, projects and topics. Immutability of `sources/` is what makes the distillation auditable later.

**(d) The payoff.** Wire design rule 14: give the top recurring producers a standing first step to consult the wiki before drafting. Add a `changelog.md` the nightly distiller appends to, so growth is visible to anyone who chooses to look. Do NOT build a weekly learning report: it is surface number two, it violates rule 2, and it will go unread.

**Traps:** two writers on one file (automation plus a human editing in the app) produce sync conflicts, so keep the user's use read-mostly and have the plugin pull on open. Over-linking is a real failure mode; density belongs in hubs. And apply rule 10 to this phase honestly: if the user has not opened the vault in three weeks, the system says so in the brief and stops maintaining view-specific extras.
**Acceptance:** the user opens the graph and clicks from a project to a counterparty to a competitor in three hops; a link they mailed themselves yesterday is a linked wiki page this morning; and a routine draft visibly cites something the user never told it in that session.

### Phase 6 — The loop: reconcile, grade, self-retire
One nightly cloud routine, scheduled AFTER the day's data is in and BEFORE the morning brief. Three scripts plus judgment:
- **prepare** (deterministic): for every open task, gather evidence snippets from the day's session digests, meeting-action extracts, and recent feedback (match by task id/code or multiple distinctive tokens); detect duplicate task pairs (title similarity or same source + token overlap); detect meta-tasks. Output a candidates file.
- **judge** (the routine's model, its ONLY judgment work): classify candidates. HARD evidence closes: explicit completion (artifact produced AND dispatched, or an explicit "done/sent" about that task, unambiguous match), exact duplicates (same action + counterparty + deliverable; keep the earlier-due or richer one), meta-tasks. SOFT evidence proposes: a meeting covered the topic without explicit completion; someone else took ownership; overtaken by newer decisions. When in doubt, propose; ambiguous match, drop.
- **apply** (deterministic guardrails in code): validate ids against the snapshot, demote firewalled domains to proposals, cap total mutations per night (~15), stamp the decisions file so it can never apply twice. Closes = status done + an evidence note (reopening is trivial); duplicates/meta = archive with reason. Append closed items to the brief's receipt surface. Maintain the proposals ledger: new proposals get a close date 72h out; any user-side event on a proposed task = veto, recorded permanently; aged-out proposals close with receipts; firewalled proposals never age.
- **grade** (deterministic): score yesterday's brief 0-10: minus 3 per closed item that resurfaced (hard fail), minus 1 per duplicate task created that day, minus 1 per user intervention (their correction events are the ground truth), minus 1 per missing receipt. Log score + a trend line (interventions/day, open tasks, auto-closes) to `state/evals/`. Make the grader idempotent: one line per date, a re-run overwrites in place. And distinguish events written by the user from events written by the system's own routines, or the grader will count its own work as user intervention and punish itself for running.
- **Weekly pass:** cluster the week's recurring corrections into durable rules (promote each into the relevant skill/instruction file, ONE commit each so any promotion reverts independently). Split system upgrades by risk: LOW-RISK (numeric thresholds, similarity ratios, noise patterns inside the loop's own scripts) auto-apply, one commit each, receipted in the next brief; STRUCTURAL (brief renderer logic, other routines, skills) render as numbered proposals in that brief for a one-line "apply 2" reply. Never park proposals in a folder the user must open.
- **Self-retirement:** with 21+ days of trend data, compare the last 7 days against the first 7 (median interventions, open tasks, resurfaced count). Improving: one trend line in the receipt. Not improving: the loop proposes its own shutdown in the brief with the numbers; 7 further days of user silence and it writes a retired flag: every future run no-ops and the next interactive session deletes the routine. The user never schedules a review.
**Acceptance:** within the first week of the loop running: at least one evidence-based close with a correct receipt, zero resurfaced closed items, and the eval score visible in the brief.

### Phase 7 — Watchdog
A manifest (JSON) listing every producer AND every mandatory phase inside every producer: ingest watermarks, brief file for today, distiller heartbeat, courier pushes, the loop's last run, the vault-maintenance pass, plus any token/credential expiry dates as countdown checks. A stdlib-only checker evaluates all of them (amber/red thresholds per component, schedule-aware so weekends don't false-alarm) and writes a health state file. Three requirements beyond the obvious, all from design rule 9: every mandatory phase asserts a named log line and a missing assertion goes amber within 24h; a **parked** state carries reason, since-date and next-check date and auto-expires so diagnosed outages stop shouting; freshness derives from content fields, never from file modification times. The checker always exits 0, because a watchdog that crashes the pipeline it watches is worse than none. The brief renders a banner only when something is non-green; a session-start hook shows the same. Any component that throws reports as amber with its error, never silently drops.
**Acceptance:** stop one producer for a day; the brief says so the next morning without anyone asking. Then delete one phase from one routine's prompt; the brief flags the missing capability within a day, rather than three weeks later by accident.

## PART 5 — THE OPERATING COVENANT (show this to the user at the end of the build)

**You:** read the brief; reply in one-liners when you want to redirect; nothing else, ever.
**The system:** ingests your sources, keeps memory current from your own sessions, keeps that memory browsable and consults it before it drafts anything, closes what the evidence says is done (receipted, reversible), proposes what it suspects (silence applies it in 72h), grades itself nightly, tunes itself weekly, and shuts itself down if it stops earning its place.
**Never, without your explicit line:** anything in your firewalled domains, any external send, any new channel you would have to check.

## PART 6 — FEASIBILITY AND DEGRADED MODES

- **Minimum viable:** Claude Code + a private GitHub repo. Without cloud routines, Phases 3 to 6 run as "when a session opens" hooks plus manual triggers; the system is reactive instead of nightly, still valuable. Phase 5 loses nothing at all: the vault, the links and the capture lanes work identically, they just refresh when a session runs rather than overnight.
- **Preferred:** cloud scheduled routines for every LLM step (ingest classification, distiller, the loop, the vault pass). Local scheduled tasks only for deterministic collectors (the session courier). Reminder: Windows headless Claude authentication is not viable for scheduled jobs; do not fight it.
- **Always-on machine:** optional. Useful for deterministic collectors and merge bridges; a flaky home server is worse than the cloud for anything scheduled. Nothing in the build path may depend on one.
- **Cost control:** routines are capped per day by plan; this design needs roughly 12-14 runs/day at steady state (8 ingest + brief + distiller + loop + weekly extras). Trim ingest frequency first if capped. Obsidian is free including commercial use; the git plugin is free; no paid starter kit is needed. Phone access to the vault is the only paid item and is never appropriate for a confidential vault.

*End of guide. Claude: begin with Part 3, the interview. Do not create any file before it.*
