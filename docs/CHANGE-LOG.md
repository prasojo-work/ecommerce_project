# Change Log

> **Append-only.** Never rewrite the past. Newest entry at the top of *History*.
> This file records every change to the agreed plan, with its rationale. The current truth
> lives in [`PLAN.md`](PLAN.md); this file records how we got there.

## History

### 2026-10-09 — v0.1.2 — Architecture baselined

**Context.** Stage 3 (architecture) produced the system, domain, and API designs and closed
the three product decisions deferred from Stage 2.

**What was added.**

- `03-architecture/ARCHITECTURE.md` — C4 context, container, and component views; bounded
  contexts; integration flow; NFR architecture; deployment topology; a Phase 2 data-platform
  outline.
- `03-architecture/DATA-MODEL.md` — ERD, tables, enumerations, indexes, money handling,
  migration and seeding strategy.
- `03-architecture/API.md` — REST contract, conventions, error envelope, and endpoints.
- `decisions/ADR-0005..0012` — API style, async & tasks, operator console, cart & guest
  merge, auth & tokens, mock-first payments, deployment stack, and image licensing.
- `_working/TODO_*` — raw system-architect, backend, frontend, data-engineer, and
  cloud-engineer files.

**Decisions closed.** `D1` → Django admin as the v1 operator console (`ADR-0007`). `D2` →
server-side cart with a guest cookie merged on login (`ADR-0008`). `D3` → in-memory access
token plus an httpOnly refresh cookie (`ADR-0009`).

**Impact.** `PLAN.md` re-baselined to v0.1.2. No application code written yet.

### 2026-10-09 — v0.1.1 — Product scope baselined

**Context.** Stage 2 (product) produced the curated scope and UX documents.

**What was added.**

- `02-product/SCOPE.md` — personas, epics `EPIC-1..7`, user stories with acceptance
  criteria, in/out of scope, NFRs `NFR-1..9`, and the v1 Definition of Done. Three open
  decisions (`D1` operator-console form, `D2` guest cart, `D3` token storage) are deferred to
  Stage 3.
- `02-product/UX.md` — visual language and design tokens, information architecture, key
  flows, states matrix, component inventory, accessibility and responsive requirements, and
  the validation plan.
- `_working/TODO_technical-project-manager.md`, `_working/TODO_ui-ux.md` — raw agent files.

**Impact.** No change to the plan itself; product detail elaborated. `PLAN.md` re-baselined
to v0.1.1. No application code written yet.

### 2026-10-09 — v0.1.0 — Project reset and re-baseline

**Context.** The repository previously contained a complete earlier iteration of this
project (brand `NORDVIK`) that was erased in commits `1bb7969` ("erase content") and
`64550f3` ("erase all"). The founder chose a **fresh start**: re-plan the project from zero
rather than resume the prior code, reusing the prior *documentation conventions* because
they were sound.

**Decisions taken in this baseline.**

- Fresh start; prior work treated as discarded (recoverable at `d23c8de` if ever needed).
- Brand **LYSHEIM** adopted (`ADR-0003`).
- Monorepo structure with `backend/`, `frontend/`, `docs/` (`ADR-0001`).
- Documentation and change-control convention reused (`ADR-0002`).
- Working agreement adopted: small increments, quality gates, unit tests, local commit
  without push, scenario-based QA, seeding, environment segregation (`ADR-0004`, see
  `WORKING-AGREEMENT.md`).
- Market changed to **international, USD** (the prior iteration targeted Indonesia/IDR).
- Stack updated to **Django 6** with an explicit async + built-in Tasks policy (see
  `PLAN.md` §5).
- Free-tier deploy targets fixed: Render (backend), Vercel (frontend), Supabase (Postgres),
  Upstash (Phase 2).

**Impact.** `PLAN.md` baselined at v0.1.0. Stage 0 (foundation) and Stage 1 (business
strategy) documentation produced. No application code written yet.
