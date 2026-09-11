# os-config.md — Personal OS configuration
<!-- Source of truth for every build phase. Written from the Phase 0 interview,
     2026-08-18, confirmed by Armando in session. Language: English (system content). -->

## 1. Domains and priority

Tracked domains, in brief display order (operational first, per Armando's choice):

| # | Domain | Slug | Scope |
|---|--------|------|-------|
| 1 | Cotizaciones y pendientes operativos | `cotizaciones-operativo` | Quotes, client follow-ups, day-to-day tasks (Cemex, TIP, Vemo, and other Draiver clients) |
| 2 | Operación Kavak | `operacion-kavak` | Kavak account operations |
| 3 | Pendientes y acuerdos en reuniones España | `reuniones-espana` | Commitments and agreements from Spain meetings (incl. Clicars operational side) |
| 4 | Grandes deals / RFPs | `grandes-deals` | Major pursuits: Uber AV Field Support RFP, Clicars fleet-optimizer pilot, successors |
| 5 | Pipeline estratégico | `pipeline-estrategico` | Automation/process initiatives: Ford, Tesla, Element trip-flow automation |
| 6 | Operación semanal y márgenes | `operacion-semanal` | Weekly reviews, team performance, margins, comms/board meetings |

**Existential priority:** none — balanced. No domain outranks the others; the order above is display order for the brief, not a weighting.

## 2. Firewalled domains

| Domain | Slug | Isolation |
|--------|------|-----------|
| Personal finance & compensation | `fw-finanzas` | Sealed inside main tree |
| Family / personal life | `fw-familia` | Sealed inside main tree |

Enforcement (must live in script code as a constant, `FIREWALLED_DOMAINS`, never only in prompts):
- Never auto-closed, never auto-processed, never cross-referenced by any routine.
- Appear in receipts only as count-only lines ("N items withheld").
- Content never leaves its folder; the reconcile loop demotes any action on them to propose-only, forever.
- No physically separate vault was chosen. NOTE: sealed-in-tree content still syncs to the private GitHub repo. See open question OQ-1.

## 3. The one surface

- **Daily brief at 09:00, America/Mexico_City** (moved from 07:00 on 2026-09-11 at Armando's request: the routines are local and the laptop is rarely on at 7). No DST since 2022; the scheduler takes local-time cron.
- **Brief language: Spanish** — tuteo, direct, English business terms acceptable (pipeline, deal, RFP).
- **System/technical content: English** (scripts, comments, system docs, this file).
- **Memory tree default language: English**, single-language per anti-drift rule; client-native terms stay in Spanish (tarifas, madrinas, etc.). Proposed by Claude, not explicitly ratified — see open question OQ-2.
- No other surfaces, ever. The wiki (Phase 5) is a library, never a queue.

## 4. Feedback covenant and code scheme

- Armando replies in one-liners; the system does everything else.
- **T-** = tasks · **A-** = new actions requiring him · **P-** = proposals.
- Every line in the brief he might respond to carries its code.

## 5. Data sources

Connected in the current session, all under the work account **armando.flores@driverdo.com** (no personal accounts connected):

| Connector | Status |
|-----------|--------|
| Gmail | connected — UNVERIFIED (empirical read-test required before Phase 3 trusts it) |
| Google Calendar | connected — UNVERIFIED |
| Google Drive | connected — verified 2026-08-18 (live search performed in-session) |
| Slack | connected — UNVERIFIED |
| Jira / Confluence | connected — UNVERIFIED |
| Salesforce | connected — UNVERIFIED |
| HubSpot | connected — UNVERIFIED |

No meeting-transcription connector present; transcripts arrive via capture lanes (§8) until one exists.

## 6. Infrastructure and plan

- **GitHub:** no account yet. Creating a personal account (not Draiver's org) is step one of Phase 1; Armando enters credentials himself, Claude never handles passwords. Repo: private.
- **Cloud scheduled routines:** available on this plan (scheduled-tasks tooling present). Daily run allowance: verify at Phase 3 before scheduling; design target ~12–14 runs/day, trim ingest frequency first if capped.
- **Local machine:** MacBook, intermittently on. The session courier (Phase 4) runs **catch-up-on-wake**, not fixed-time: whenever the machine is up, it processes the backlog. No always-on machine; nothing in the build may depend on one.
- Platform: macOS — the Windows headless-auth trap does not apply, but the courier stays deterministic (no LLM) regardless.

## 7. Autonomy appetite

**Recommended default** (start here, widen later):
- Hard evidence → acts automatically, receipt in the brief.
- Soft evidence → proposal with 72h silence-consent; one veto = that item is never proposed again.
- Firewalled domains → propose-only forever.
- External sends (email, messages, anything leaving the system) → always require explicit confirmation.

## 8. Second brain (Phase 5)

Capture lanes (all four chosen):
1. Links/articles Armando sends himself (email keyword or pasted into any session).
2. Documents & decks (watched folder or pasted into a session).
3. Meeting transcripts & notes.
4. Links colleagues share (Slack or email threads).

Six-month brain uses → topic hubs to build:
- **Client & deal history** — decisions, tarifas, commitments per client ("what did we agree with Kavak in March and why?").
- **People context before meetings** — who is X, what do they care about, what's pending.
- **Competitive & market intel** — AV market, fleet logistics, competitor reading.
- **Pricing & tarifas history** — every quote, route pricing, won/lost.

## Resolved questions

- **OQ-1 (firewall depth): RESOLVED 2026-08-18 — keep sealed in tree.** Armando accepts that firewalled content syncs to the private GitHub repo; isolation is enforced in script code (never processed, never cross-referenced, count-only receipts). Consequence: git remote traffic must use SSH, not HTTPS (see network note below).
- **OQ-2 (tree language): RESOLVED 2026-08-18 — Spanish.** The memory tree is written in Spanish (Armando's working language and what he will browse). Scripts, code comments, and system docs remain in English. Brief in Spanish per §3.

## Network note (2026-08-18)

The office network performs TLS interception via a FortiGate firewall (github.com presents a cert issued by `CN=FG100FTK20017309, O=Fortinet`). Consequences, encoded as build constraints:
- Git remote transport: **SSH only** (deploy via SSH key). HTTPS git would fail cert validation or, worse, expose repo contents in transit to the corporate middlebox — unacceptable given firewalled content lives in-tree.
- Armando must never type personal credentials (GitHub password) through this network; account creation happens on cellular/home network.
- The watchdog (Phase 7) should treat "SSH to github.com blocked on office network" as a possible parked state, since some firewalls block port 22; fallback is SSH-over-443 (ssh.github.com:443).
