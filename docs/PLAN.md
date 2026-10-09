# Master Plan — LYSHEIM (home-goods e-commerce)

> **Status:** Living document · **Baseline version:** v0.1.0 (2026-10-09) · **Owner:** Founder (solo)
> This file always reflects the *current* agreed plan. The history of changes lives in
> [`CHANGE-LOG.md`](CHANGE-LOG.md).

---

## 1. Vision

> Build a curated, design-led home-goods store for an international market that makes
> well-made, affordable everyday furniture and homeware easy to buy online — and, in
> building it, demonstrate that one engineer can carry a product from market insight to a
> production-grade, well-governed, deployed system.

LYSHEIM is **a simulated business used as a portfolio artifact**: the strategy is researched
as if the store were real, while the *build* is scoped to what a solo developer can finish,
ship, and keep polished.

## 2. Goals & success criteria

**Primary goal (portfolio):** a public artifact a recruiter or freelance client can open
and, within a minute, conclude *"this person can be trusted to handle my problem."*

- [ ] `GOAL-1` A live, publicly reachable demo (storefront + operator console) with a seeded catalog.
- [ ] `GOAL-2` A business strategy a non-technical reader finds credible.
- [ ] `GOAL-3` Clean, tested, typed code across backend and frontend, with CI green on every change.
- [ ] `GOAL-4` Documentation that shows the plan *and* how it changed.
- [ ] `GOAL-5` An observable, documented path from local dev to cloud deploy on free tiers.
- [ ] `GOAL-6` *(Phase 2)* A data-engineering track (events → warehouse → dashboard) that turns the store into a differentiated portfolio piece.

**Explicit non-goals (for now):** real payment capture, real logistics integration, real
customer acquisition, multi-tenant/marketplace, native mobile apps, multi-currency.

## 3. Scope

### MVP (Phase 1 — the store works end to end)

- [ ] Catalog: categories, products, variants, images, stock.
- [ ] Browse: category listing, product detail, search + filter + sort.
- [ ] Cart: add / update / remove, persisted server-side for signed-in users.
- [ ] Checkout: address, shipping method (simulated), payment (**mock/sandbox**).
- [ ] Orders: order confirmation, history, and detail for the customer.
- [ ] Accounts: register, login (JWT access + refresh), profile, addresses.
- [ ] Operator console: manage products, categories, inventory, images, and order status.
- [ ] Foundations: CI, tests, lint/type gates, Docker Compose, deploy to free tier.

### Phase 2 (deferred until the store is solid)

- [ ] **Data-engineering track** (the author's specialty): event capture → warehouse → dashboards.
- [ ] Analytics, recommendations, reviews, wishlist, promo codes, real payment gateway.

### Out of scope (indefinitely)

- Multi-vendor marketplace, real inventory logistics, loyalty programs, multi-currency,
  native apps.

> Rationale for the Phase 1 / Phase 2 split: in a real retail business the data team arrives
> *after* the business is operating and generating data. Reproducing that order keeps the
> story honest.

## 4. Technology stack

| Layer | Choice | Notes |
|---|---|---|
| Backend | Python + **Django 6** + **Django Ninja** | `uv` for deps, `ruff` lint/format, `basedpyright` types |
| Database | **PostgreSQL** | Local via Docker Compose; Supabase (Postgres) in the cloud |
| Frontend | **Next.js** (React, TypeScript, App Router) | `pnpm`, Prettier, ESLint, `tsc` |
| Auth | **JWT** (access + refresh) | Decoupled SPA talking to Django over HTTP |
| Contracts | **REST** (`/api/v1/`) + OpenAPI schema | Ninja auto-generates the schema the frontend consumes |
| Background work | **Django 6 Tasks framework** | Built-in `@task`; no Celery for v1 |
| Env | Docker Compose (local) | Postgres + backend + frontend |
| Cloud | Render · Supabase · Vercel · (Upstash, Phase 2) | Free tiers |
| CI/CD | GitHub Actions | Lint, type-check, tests, build |

The stack is expected to grow with the business; additions are recorded as ADRs.

## 5. Architecture at a glance

Decoupled **monorepo**: a Django API and a Next.js client, each independently buildable,
communicating over HTTP/JSON. Local orchestration with Docker Compose. Full detail in
`03-architecture/ARCHITECTURE.md` (Stage 3).

```
ecommerce_project/
├── backend/     Django + Ninja API  ──/api/v1/──▶  frontend/   Next.js web app
├── frontend/
└── docs/
```

### Async policy (Django 6)

Django 6 (released Dec 2025) ships a built-in **Tasks framework**, async pagination, and
deeper async support out of the box. Our policy:

- Serve via **ASGI** (Uvicorn) in both development and production.
- Use **`async def`** handlers for I/O-bound endpoints (e.g. the mock payment gateway call).
- Use the **async ORM** (`acreate`, `aget`, `afilter`, `async for`) where it removes real
  blocking; stay pragmatic and keep synchronous code where async adds no value.
- Use the **built-in Tasks framework** (`@task`) for off-request work: order-confirmation
  email (mocked), analytics/event emission (Phase 2), image processing. This avoids adding
  Celery to a project that does not need it.
- Enable the built-in **Content Security Policy** support as part of security hardening.

> Rationale: async is used where it is appropriate, not evangelically. The goal is a
> demonstrative, honest use of the framework's modern capabilities.

## 6. Milestones

| ID | Milestone | Outcome |
|---|---|---|
| M0 | Foundations | Repo, CI, Docker Compose, both apps boot |
| M1 | Catalog & browse | Products visible and navigable |
| M2 | Accounts & auth | Register / login, JWT flow working |
| M3 | Cart | Server-side cart for signed-in users |
| M4 | Checkout & orders | Mock payment → order created → history |
| M5 | Operator console | Manage catalog and orders |
| M6 | Hardening | Tests, a11y, performance, security pass |
| M7 | Deploy | Live demo on free tier |
| M8 | Data-engineering track | Phase 2 (event pipeline + dashboard) |

Detail, dependencies, and sequencing land in `04-delivery/ROADMAP.md` (Stage 4).

## 7. Delivery approach

- **Solo developer wearing many hats.** Each `the_team/` role is a lens during planning;
  every decision is owned by the founder.
- **Planning-first.** No application code until the relevant slice of the plan is baselined.
- **Assistant-authored, founder-reviewed.** Work proceeds in small increments. The assistant
  writes the code, keeps it passing every quality gate (`ruff`, `basedpyright`, ESLint,
  `tsc`, tests, build), adds unit tests, and commits each increment; the founder reviews and
  decides whether to continue. See [`WORKING-AGREEMENT.md`](WORKING-AGREEMENT.md) and
  `ADR-0004`.

## 8. Governance — how the plan changes

Simulated start-up: the plan is expected to move. Changes are handled deliberately:

1. Capture the decision as an **ADR**.
2. Append the delta and rationale to [`CHANGE-LOG.md`](CHANGE-LOG.md).
3. Re-baseline this file and bump its version.

See `ADR-0002`.

## 9. Top risks

Full register in `04-delivery/ROADMAP.md` (Stage 4). Headlines:

- `RISK-1` **Scope creep** — e-commerce can absorb infinite features. Mitigation: hard MVP
  boundary + change control.
- `RISK-2` **Free-tier cold starts** — the demo sleeps and the first click is slow.
  Mitigation: keep-alive ping; documented in the deploy ADR.
- `RISK-3` **Portfolio thinness** — a "toy" store impresses no one. Mitigation: a real
  domain model, tests, and a deployed live demo.
- `RISK-4` **Infinite re-planning / stalled momentum** — the number-one way portfolio
  projects die. Mitigation: thin vertical slices that are always demoable; a fixed finish
  line for v1.
- `RISK-5` **Image licensing** — the reference images are Creative Commons (some `BY-SA`,
  some `BY-ND`). Mitigation: an attribution/credits page and an ADR recording the policy.

## 10. Document index

- Business: [`01-business/STRATEGY.md`](01-business/STRATEGY.md)
- Product: [`02-product/SCOPE.md`](02-product/SCOPE.md), [`02-product/UX.md`](02-product/UX.md)
- Architecture: `03-architecture/ARCHITECTURE.md`, `03-architecture/DATA-MODEL.md` (Stage 3)
- Delivery: `04-delivery/ROADMAP.md` (Stage 4)
- QA: `05-qa/` (scenarios + results)
- Process: [`WORKING-AGREEMENT.md`](WORKING-AGREEMENT.md)
- Decisions: [`decisions/`](decisions/)
- Change history: [`CHANGE-LOG.md`](CHANGE-LOG.md)

---

### Revision history

| Version | Date | Summary |
|---|---|---|
| v0.1.0 | 2026-10-09 | Initial baseline re-established after the project reset. Brand `LYSHEIM`; working agreement; Stage 0/1 docs. |
| v0.1.1 | 2026-10-09 | Product scope and UX baselined (Stage 2). |
