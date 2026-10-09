# Change Log

> **Append-only.** Never rewrite the past. Newest entry at the top of *History*.
> This file records every change to the agreed plan, with its rationale. The current truth
> lives in [`PLAN.md`](PLAN.md); this file records how we got there.

## History

### 2026-10-10 — v0.1.9 — M0.8 seed command skeleton landed

**Context.** The last M0 increment: a seeding entry point that later milestones fill in, so the
command's contract is fixed before there is any data to seed.

**What was added.**

- `core/seeding.py` — a registry of `SeedStep` entries. A step carries a `name`, an idempotent
  `run` callable, and an optional `clear` hook used by `--reset`.
- `core/management/commands/seed.py` — `manage.py seed`. Runs every registered step in
  registration order inside a single transaction; `--reset` calls each `clear` hook first, in
  reverse registration order.
- `tests/test_seed.py` — nine tests covering ordering, the `--reset` hook, steps with no
  `clear`, the empty-registry path, fail-fast, and the registry's snapshot semantics.

**Decisions taken.**

- **A registry, not hard-coded seeding.** With no models until `M1.1`, the only way to make the
  two properties the roadmap asks for — *idempotent* and `--reset` — real and testable is for
  the command to execute something. The registry is that seam: `M1.2` registers the catalog
  seeders without touching the command.
- **One transaction for the whole run.** A failure part-way through leaves neither a
  half-seeded database nor, under `--reset`, a wiped-but-unfilled one. The run aborts instead of
  reporting success, which `test_a_failing_step_aborts_the_run` pins.
- **`clear` hooks run in reverse registration order**, so rows are deleted before the rows they
  depend on.
- **Idempotency is a contract on each step, not something the command can enforce.** The
  skeleton proves the command's mechanics; every real seeder is responsible for its own
  re-runnability, and `M1.2` must cover that with its own tests.

**Impact.** Every M0 increment has landed, and `uv run python manage.py seed` runs with and
without `--reset`. Backend gates green — `ruff format --check` (26 files), `ruff check`,
`basedpyright` (0 errors), `pytest` (17 passed, up from 8).

The M0 milestone row stays `[~]` rather than `[x]`: its exit criteria include "CI passes", and
the `M0.9` workflows have not yet run on GitHub, because pushing is the founder's call
(`WORKING-AGREEMENT.md` §1.4). M0 closes once the first push goes green.

### 2026-10-10 — v0.1.8 — M0.9 continuous integration landed

**Context.** With the compose stack proven, M0.9 wired the quality gates into GitHub Actions so
a push or a pull request is checked without anyone running the commands by hand.

**What was added.**

- `.github/workflows/backend.yml` — `ruff format --check`, `ruff check`, `basedpyright`, and
  `pytest`, on Python provisioned by `uv` from the lockfile.
- `.github/workflows/frontend.yml` — `pnpm typecheck`, `lint`, `format:check`, `test`, and
  `build`, on Node 24 with the pnpm store cached.
- Both are path-filtered (`backend/**` and `frontend/**`), so a change to one app does not run
  the other's gates; each also re-runs when its own workflow file changes.

**Decisions taken.**

- **Native path filters across two workflows.** The roadmap asks for "path-filtered jobs".
  Job-level filtering inside a single workflow needs a third-party action such as
  `dorny/paths-filter`; two workflows using `on.push.paths` / `on.pull_request.paths` reach the
  same result with no extra dependency. The trade-off is that a docs-only change reports no
  checks at all instead of a green skip. Acceptable while `main` is unprotected.
- **The backend job runs a real PostgreSQL service.** Settings fall back to SQLite only when
  `DATABASE_URL` is empty, so leaving it unset would have tested an engine the project never
  deploys on. The job provisions PostgreSQL 17 — the same version as `compose.yml`.
- **Actions are pinned to major tags** (`checkout@v6`, `setup-uv@v8`, `pnpm/action-setup@v4`,
  `setup-node@v7`) rather than commit SHAs. Major tags are the ecosystem norm and stay readable;
  SHA pinning is the stronger supply-chain posture and is worth revisiting before the project
  faces real customers.
- `pnpm` is pinned to `12.3.4` in the workflow to match `packageManager` in
  `frontend/package.json`; the two must move together.
- Concurrency groups cancel a superseded run on the same ref, so a quick second push does not
  queue behind the first.

**Impact.** The CI configuration is complete and was validated locally with `actionlint`, and
the backend suite was re-run against PostgreSQL 17 before the commit. The workflows have
**not** executed on GitHub — the working agreement has the assistant commit locally and the
founder decide when code reaches GitHub — so the M0 exit criterion "CI passes" stays unverified
until the first push. M0 is down to `M0.8` (seed command).

### 2026-10-10 — v0.1.7 — M0.7 compose stack landed

**Context.** Both apps booted on the host; M0.7 made the whole system start with one command so
a reviewer can run the demo without installing Python, Node, or Postgres.

**What was added.**

- `compose.yml` — Postgres 17, the API, and the web app, with health-gated start ordering and a
  named `db-data` volume. Every connection value comes from the environment with a local
  default, so `docker compose up --build` needs no `.env` file.
- `backend/Dockerfile` — `python:3.13-slim` with `uv`; dependencies install from the lockfile
  into `/opt/venv` in a cached layer, then the source is copied. Runs Uvicorn on the ASGI app.
- `frontend/Dockerfile` — multi-stage Node 24 with `pnpm`; dependencies install from the
  lockfile, `pnpm build` runs in the builder, and the runner starts the built app.
- `backend/.dockerignore`, `frontend/.dockerignore` — keep host artefacts (`.venv`,
  `node_modules`, `.next`, `db.sqlite3`) and the local `.env` out of the build context.

**Decisions taken.**

- The API container runs `manage.py migrate --noinput` before Uvicorn. Migrations are
  idempotent, so a fresh volume needs no manual step and a restart is harmless.
- The Postgres port is **not** published to the host by default. Only database clients need it,
  and leaving it closed avoids a collision on a machine that already runs Postgres; the entry
  ships commented in `compose.yml`.
- The web image runs the **production** build (`pnpm build` → `pnpm start`) rather than
  `pnpm dev`, so the container exercises the artefact that actually ships. A Next.js
  `standalone` output would shrink the image further, but it interacts badly with `pnpm`'s
  symlinked `node_modules`; that optimisation is deferred until image size matters.
- No source bind-mounts. Compose is the "does the whole system work together" path; the fast
  edit loop stays on the host (`uv run uvicorn --reload`, `pnpm dev`), as the runbook documents.

**Impact.** `docker compose up --build` brings up all three services from a clean checkout.
Remaining M0 items: `M0.9` CI, then `M0.8` seed command.

### 2026-10-09 — v0.1.6 — M0 frontend skeleton landed

**Context.** With the backend skeleton committed, M0 continued with the Next.js application so
both apps boot and the quality gates cover both sides.

**What was added.**

- `frontend/` — Next.js 16.4 (App Router, RSC, Turbopack) with TypeScript `strict`, managed by
  `pnpm`.
- The design tokens from `UX.md` §2 are now the single source of truth in
  `src/app/globals.css` (the `--lys-*` custom properties), with a minimal base layer: warm
  canvas, ink text, a visible `:focus-visible` ring, and image defaults.
- `src/app/layout.tsx` — `lang="en"`, Inter through `next/font`, LYSHEIM metadata.
- `src/app/page.tsx` — a minimal branded placeholder (one `<h1>`, one `<main>` landmark).
- Tooling: ESLint 9 flat config (`core-web-vitals` + `typescript` + `eslint-config-prettier`),
  Prettier, `vitest`, and a root `.editorconfig`.
- Gate scripts: `typecheck`, `lint`, `format:check`, `test`, `build`.
- `src/lib/config.ts` — `getApiBaseUrl()` reads `NEXT_PUBLIC_API_BASE_URL` with a localhost
  fallback, covered by two tests.
- `frontend/.env.example` documenting `NEXT_PUBLIC_API_BASE_URL`.

**Decisions taken.**

- **No styling framework.** The docs specify design tokens in `globals.css` and never mention
  Tailwind, so the scaffold uses plain CSS with `--lys-*` tokens plus CSS Modules. Adopting a
  CSS framework is deferred to its own ADR before the catalog UI is built at `M1.5`.
- `typecheck` runs `next typegen && tsc --noEmit` — Next 16 generates `LayoutProps` and the
  route types, so a bare `tsc --noEmit` fails on a fresh checkout.
- The vitest config uses the `.mts` extension so Vite loads it as ESM.
- `@types/node` raised to `^24` to match the Node runtime and satisfy `vitest@5`'s peer range.

**Impact.** Both applications boot. Backend gates unchanged and green. Frontend gates green:
`lint`, `format:check`, `vitest` (2 passed), `typecheck`, `build` (4 static pages). Boot smoke
test: `GET /` returns 200 and renders `LYSHEIM`. Remaining M0 items: `M0.7` compose, `M0.8`
seed command, `M0.9` CI.

### 2026-10-09 — v0.1.5 — M0 backend skeleton landed

**Context.** Planning closed at v0.1.4. M0 (foundations) began with the backend skeleton —
the Django 6 + Django Ninja service every later increment builds on.

**What was added.**

- `backend/` — a `uv`-managed project: `config/` (settings split `base`/`dev`/`prod`, URL
  config, Ninja API instance, ASGI and WSGI entrypoints), `core/` (request-ID middleware,
  health view, JSON log formatter), `manage.py`, `pyproject.toml`, `uv.lock`, `.env.example`,
  `README.md`.
- `GET /healthz` returns `{"status": "ok", "request_id": ...}` and always sets an
  `X-Request-ID` response header, echoing a caller-supplied value when present.
- API surface under `/api/v1`: `GET /api/v1/openapi.json` and `GET /api/v1/docs`.
- `tests/` — four pytest tests covering the health contract and the OpenAPI schema.
- Configuration is environment-only (`django-environ`), with a SQLite fallback so a bare
  checkout and the test suite run without infrastructure; PostgreSQL is used via
  `DATABASE_URL`.

**Decisions taken.**

- `uvicorn[standard]` added as a runtime dependency — it serves both local runs and the
  Render deploy, and `uv run uvicorn config.asgi:application` is the documented run command.

**Impact.** First application code in the fresh-start repository. All gates green:
`ruff format --check` (19 files), `ruff check`, `basedpyright` (0 errors), `pytest` (4
passed). ASGI smoke test: `/healthz` → `200`, `/api/v1/openapi.json` → `200`. `PLAN.md` is
unchanged at v0.1.4.

### 2026-10-09 — v0.1.4 — Quality standards baselined (planning phase complete)

**Context.** Stage 5 (cross-cutting) produced the security, review, and collaboration
standards, closing the planning phase.

**What was added.**

- `06-quality/SECURITY-BASELINE.md` — scope and data classification, trust boundaries, a
  STRIDE threat model, twelve findings (`SEC-FIND-1.1..12`) with risk and remediation, a
  secure-configuration baseline, detection/incident-response, and privacy handling.
- `06-quality/CODE-REVIEW-STANDARD.md` — the review ritual, severity levels, and the checklist
  that must pass before any commit.
- `06-quality/AGENT-TOPOLOGY.md` — the founder/assistant/tester-agent topology, handoff
  contracts, communication protocol, memory model, failure recovery, and evaluation signals.
- `_working/TODO_cybersecurity.md`, `TODO_code-reviewer.md`, `TODO_multi-agent-orchestrator.md`.

**Impact.** `PLAN.md` re-baselined to v0.1.4. **The planning phase (Stages 0–5) is complete.**
No application code written yet; the next step is M0 (foundations).

### 2026-10-09 — v0.1.3 — Delivery plan baselined

**Context.** Stage 4 (delivery) turned the workstreams into a sequenced, incremented roadmap
and formalised delivery governance.

**What was added.**

- `04-delivery/ROADMAP.md` — milestones `M0`–`M8` with concrete increments, sequencing and
  dependencies, RACI, Definition of Done, and change control.
- `04-delivery/RISK-REGISTER.md` — the full register `RISK-1..9`, reviewed at every milestone
  gate.
- `04-delivery/RUNBOOK.md` — the runbook skeleton, filled in one entry per increment.
- `_working/TODO_technical-lead.md` — raw technical-lead file; `_working/TODO_technical-project-manager.md`
  extended with the Stage 4 items.

**Impact.** `PLAN.md` re-baselined to v0.1.3. No application code written yet.

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
