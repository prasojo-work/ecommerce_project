# Master Plan — NORDVIK (home-goods e-commerce)

> **Status:** Living document · **Baseline version:** v0.1.2 (2026-10-07) · **Owner:** Founder (solo)
> This file always reflects the *current* agreed plan. History of changes lives in [`CHANGE-LOG.md`](CHANGE-LOG.md).

---

## 1. Vision

> Build a home-goods store that makes well-designed, affordable everyday furniture and homeware easy to buy online — and, in building it, demonstrate that one engineer can carry a product from market insight to a production-grade, well-governed system.

NORDVIK is **portfolio-as-simulated-business**: the strategy is researched as if the store were real, but the *build* is scoped to what a solo developer can finish, ship, and keep polished.

## 2. Goals & success criteria

**Primary goal (portfolio):** a public artifact a recruiter or freelance client can open and immediately see (a) commercial reasoning, (b) senior backend/frontend engineering, (c) disciplined documentation and change management.

- [ ] `GOAL-1` A live, publicly reachable demo (storefront + admin) with seeded catalog data.
- [ ] `GOAL-2` A business strategy a non-technical reader finds credible.
- [ ] `GOAL-3` Clean, tested, typed code across backend and frontend.
- [ ] `GOAL-4` Documentation that shows the plan *and* how it changed.
- [ ] `GOAL-5` An observable, documented path from local dev to cloud deploy.

**Explicit non-goals (for now):** real payment capture, real logistics integration, real customer acquisition, multi-tenant/marketplace, native mobile apps.

## 3. Scope

### MVP (Phase 1 — the store works end to end)
- [x] Catalog: categories, products, variants, images, stock.
- [x] Browse: category listing, product detail, search + filter + sort.
- [x] Cart: add/update/remove, persisted server-side for logged-in users.
- [x] Checkout: address, shipping method (simulated), payment (**mock/sandbox**).
- [x] Orders: order history + order detail for the customer.
- [x] Accounts: register, login (JWT access + refresh), profile, addresses.
- [ ] Admin: manage products, categories, inventory, and orders.
- [ ] Foundations: CI, tests, lint/type checks, Docker Compose, deploy to free tier.

### Phase 2 (deferred until the store is solid)
- [ ] **Data-engineering track** (the author's specialty): event capture → warehouse → dashboards.
- [ ] Analytics, recommendations, reviews, wishlist, promo codes, real payment gateway.

### Out of scope (indefinitely)
- Multi-vendor marketplace, real inventory logistics, loyalty programs, multi-currency, native apps.

> Rationale for the Phase 1 / Phase 2 split: in a real retail business the data team arrives *after* the business is operating and generating data. Simulating that order keeps the story honest. See `ADR-0004` (payment) and the Phase 2 note in [`04-delivery/ROADMAP.md`](04-delivery/ROADMAP.md).

## 4. Technology stack

| Layer | Choice | Notes |
|---|---|---|
| Backend | Python + **Django** + **Django Ninja** | `uv` for deps, `ruff` for lint/format, `basedpyright` for types |
| Database | **PostgreSQL** | Local via Docker Compose; Supabase (Postgres) in the cloud |
| Frontend | **Next.js** (React, TypeScript) | `pnpm`, Prettier, ESLint, `tsc` |
| Auth | **JWT** (access + refresh) | Decoupled SPA talking to Django over HTTP |
| Contracts | **REST** (`/api/v1/`), OpenAPI schema | Ninja auto-generates the schema the frontend consumes |
| Env | Docker Compose (local) | Postgres + backend + frontend |
| Cloud | Render · Supabase · Vercel · (Upstash, Phase 2) | Free tiers; see `ADR-0005` |
| CI/CD | GitHub Actions | Lint, type-check, tests, build |

The stack is expected to grow with the business; additions are recorded as ADRs.

## 5. Architecture at a glance

Decoupled **monorepo**: a Django API and a Next.js client, each independently buildable, communicating over HTTP/JSON. Local orchestration with Docker Compose. Full detail in [`03-architecture/ARCHITECTURE.md`](03-architecture/ARCHITECTURE.md).

```
ecommerce_project/
├── backend/     Django + Ninja API  ──/api/v1/──▶  frontend/   Next.js web app
├── frontend/
└── docs/
```

## 6. Milestones

| ID | Milestone | Outcome |
|---|---|---|
| M0 | Foundations | Repo, CI, Docker Compose, both apps boot |
| M1 | Catalog & browse | Products visible and navigable |
| M2 | Accounts & auth | Register/login, JWT flow working |
| M3 | Cart | Server-side cart for logged-in users |
| M4 | Checkout & orders | Mock payment → order created → history |
| M5 | Admin | Manage catalog and orders |
| M6 | Hardening | Tests, a11y, performance, security pass |
| M7 | Deploy | Live demo on free tier |
| M8 | Data-engineering track | Phase 2 (event pipeline + dashboard) |

Detail, dependencies, and sequencing in [`04-delivery/ROADMAP.md`](04-delivery/ROADMAP.md).

## 7. Delivery approach

- **Solo developer wearing many hats.** Each `the_team/` role is used as a lens during planning; every decision is owned by the founder.
- **Planning-first.** No application code until the relevant slice of the plan is baselined.
- **Assistant-authored, founder-reviewed.** Work proceeds in small increments. The assistant writes the code directly, keeps it passing all quality gates (`ruff`, `basedpyright`, ESLint, `tsc`, tests, build), adds unit tests, and commits each increment; the founder reviews the increment and decides whether to continue or request changes. (Superseded the earlier "teaching mode" — see `ADR-0009`.)

## 8. Governance — how the plan changes

Simulated start-up: the plan is expected to move. Changes are handled deliberately:

1. Capture the decision as an **ADR**.
2. Append the delta + rationale to [`CHANGE-LOG.md`](CHANGE-LOG.md).
3. Re-baseline this file (`PLAN.md`) and bump its version.

See [`decisions/ADR-0006-documentation-and-change-control.md`](decisions/ADR-0006-documentation-and-change-control.md).

## 9. Top risks

Full register in [`04-delivery/ROADMAP.md`](04-delivery/ROADMAP.md#risk-register). Headlines:

- `RISK-1` **Scope creep** — an e-commerce app can absorb infinite features. Mitigation: hard MVP boundary + change control.
- `RISK-2` **Free-tier cold starts** — the demo sleeps, first click is slow. Mitigation: keep-alive ping; documented in `ADR-0005`.
- `RISK-3` **Portfolio thinness** — a "toy" store impresses no one. Mitigation: real domain model, tests, and deployed live demo.
- `RISK-4` **Solo burnout / stalled momentum** — Mitigation: thin vertical slices that are always demoable.

## 10. Document index

- Business: [`01-business/STRATEGY.md`](01-business/STRATEGY.md)
- Product: [`02-product/SCOPE.md`](02-product/SCOPE.md), [`02-product/UX.md`](02-product/UX.md)
- Architecture: [`03-architecture/ARCHITECTURE.md`](03-architecture/ARCHITECTURE.md), [`03-architecture/DATA-MODEL.md`](03-architecture/DATA-MODEL.md)
- Delivery: [`04-delivery/ROADMAP.md`](04-delivery/ROADMAP.md)
- Decisions: [`decisions/`](decisions/)
- Change history: [`CHANGE-LOG.md`](CHANGE-LOG.md)

---

### Revision history

| Version | Date | Summary |
|---|---|---|
| v0.1.0 | 2026-10-04 | Initial baseline established. |
| v0.1.1 | 2026-10-04 | Brand name `NORDVIK` approved (`ADR-0007`). |
| v0.1.2 | 2026-10-07 | Delivery approach: assistant authors code; founder reviews; commit per increment (`ADR-0009`). |
