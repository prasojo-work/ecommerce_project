# Delivery Roadmap — LYSHEIM

> Consulted hats: **Senior Technical Lead** and **Senior Technical Project Manager**. Owner:
> Founder. Inputs: [`../PLAN.md`](../PLAN.md), [`../02-product/SCOPE.md`](../02-product/SCOPE.md),
> [`../03-architecture/ARCHITECTURE.md`](../03-architecture/ARCHITECTURE.md).
> Execution rules live in [`../WORKING-AGREEMENT.md`](../WORKING-AGREEMENT.md).

---

## 1. How to read this

Work is sliced into **milestones** (`M0`–`M8`) and, within each, into **increments** — each
increment is one small, demoable, committed step that passes every quality gate and carries
unit tests. An increment is the unit of the working agreement; a milestone is a
reviewer-visible capability.

Status legend: `[ ]` planned · `[~]` in progress · `[x]` done.

## 2. Milestone overview

| ID | Milestone | Outcome | Exit criteria | Status |
|---|---|---|---|---|
| M0 | Foundations | Both apps boot, gates wired, CI green | `docker compose up` runs API + web; CI passes | `[ ]` |
| M1 | Catalog & browse | Products visible and navigable | Browse → PDP works with seeded data | `[ ]` |
| M2 | Accounts & auth | Register/login works | JWT flow + refresh exercised by tests | `[ ]` |
| M3 | Cart | Server-side cart for guests + users | Add/update/remove + merge on login | `[ ]` |
| M4 | Checkout & orders | Mock purchase end to end | Order created, paid, history shown | `[ ]` |
| M5 | Operator console | Catalog/stock/orders manageable | Admin manages products + order status | `[ ]` |
| M6 | Hardening | Quality evidence produced | a11y/perf/security reports committed | `[ ]` |
| M7 | Deploy | Public demo live | Live URL passes a smoke journey | `[ ]` |
| M8 | Data track (Phase 2) | Analytics on real events | Funnel dashboard built on events | `[ ]` |

## 3. Milestone detail

### M0 — Foundations

- [ ] `M0.1` Backend scaffold: `uv` project, Django 6, Django Ninja, settings split by env.
- [ ] `M0.2` Frontend scaffold: Next.js (App Router, TypeScript strict), `pnpm`, design tokens → `globals.css`.
- [ ] `M0.3` Root tooling: `ruff` + `basedpyright` (standard) config; ESLint + Prettier; `.editorconfig`.
- [ ] `M0.4` Test harness: `pytest` (backend), `vitest` (frontend), one trivial test each.
- [ ] `M0.5` `/healthz` endpoint + JSON logging + request-id middleware.
- [ ] `M0.6` `.env.example`, `django-environ` wiring, secrets excluded from git.
- [ ] `M0.7` `compose.yml` (Postgres + API + web) with a one-command start.
- [ ] `M0.8` `seed` management command skeleton (idempotent, `--reset`).
- [ ] `M0.9` GitHub Actions CI: path-filtered jobs for backend and frontend gates.

### M1 — Catalog & browse

- [ ] `M1.1` Catalog models + migrations (`Category`, `Product`, `ProductVariant`, `ProductImage`, `ImageCredit`).
- [ ] `M1.2` Seed catalog: categories, products, variants, stock; import curated images + credits from `some_source/`.
- [ ] `M1.3` Catalog read API (`/categories`, `/products`, `/products/{slug}`) + OpenAPI.
- [ ] `M1.4` Generate the frontend API client types from OpenAPI.
- [ ] `M1.5` Catalog listing page (grid, pagination, skeletons, empty state).
- [ ] `M1.6` Product detail page (gallery, price, availability, add-to-cart placeholder).
- [ ] `M1.7` Search, filter, and sort with shareable URL state.
- [ ] `M1.8` Home page (hero + featured).
- [ ] `M1.9` `/pages/credits` attribution page (`US-6.1`).

### M2 — Accounts & auth

- [ ] `M2.1` Custom `User` model + `Address` model + migrations.
- [ ] `M2.2` Auth endpoints: register, login, refresh, logout, me (`ADR-0009`).
- [ ] `M2.3` Throttling + refresh origin/CSRF guard; tests for rate limit and bad credentials.
- [ ] `M2.4` Frontend session: in-memory access token + silent refresh interceptor.
- [ ] `M2.5` Login / register pages with validation.
- [ ] `M2.6` Profile + addresses CRUD (API and UI).

### M3 — Cart

- [ ] `M3.1` `Cart` / `CartItem` models; signed guest cookie resolution (`ADR-0008`).
- [ ] `M3.2` Cart API: get, add, update, remove; server-side stock validation.
- [ ] `M3.3` Guest-cart merge on login.
- [ ] `M3.4` Cart UI: line items, quantity stepper, totals, empty state.

### M4 — Checkout & orders

- [ ] `M4.1` `Order` / `OrderItem` / `OrderEvent` models; guarded status transitions.
- [ ] `M4.2` `/checkout/quote` (shipping options + totals).
- [ ] `M4.3` Idempotent order creation (`Idempotency-Key`) + stock decrement.
- [ ] `M4.4` `PaymentGateway` port + mock adapter; confirm/fail endpoints (`ADR-0010`).
- [ ] `M4.5` Order-confirmation email via the Tasks framework (mocked transport).
- [ ] `M4.6` Checkout UI: address → shipping → payment → confirmation.
- [ ] `M4.7` Order history and order-detail pages.

### M5 — Operator console

- [ ] `M5.1` Django admin customisation for catalog (list filters, search, inline images).
- [ ] `M5.2` Admin for orders with valid status transitions + audit visible.
- [ ] `M5.3` Operator runbook entry (create `is_staff` operator; day-to-day actions).

### M6 — Hardening

- [ ] `M6.1` Coverage push on domain/services (≥ 80%) + tests for edge cases.
- [ ] `M6.2` Accessibility pass (axe on key routes) + fixes → `ACCESSIBILITY-REPORT.md`.
- [ ] `M6.3` Performance pass (LCP budget, caching, image optimisation) → `PERFORMANCE-REPORT.md`.
- [ ] `M6.4` Security hardening (CSP, headers, throttles, secret guard, dependency audit) → `SECURITY-REVIEW.md`.
- [ ] `M6.5` End-to-end verification of the error envelope + request ids.

### M7 — Deploy

- [ ] `M7.1` `backend/Dockerfile`; Render service + worker configuration.
- [ ] `M7.2` Supabase project, pooler settings, run migrations.
- [ ] `M7.3` Vercel project + environment variables.
- [ ] `M7.4` Seed the demo database and run a smoke journey in production.
- [ ] `M7.5` Keep-alive ping + finalise the runbook.
- [ ] `M7.6` README with screenshots, architecture diagram, and the live URL.

### M8 — Data track (Phase 2, deferred)

- [ ] `M8.x` Per `ARCHITECTURE.md` §9 and `_working/TODO_data-engineer.md`; ADRs written at the start of Phase 2.

## 4. Sequencing & dependencies

`M0 → M1 → M2 → M3 → M4 → M5 → M6 → M7`, then `M8`. Cart (M3) depends on Catalog (M1) and
Identity (M2); Checkout (M4) depends on Cart; Operator (M5) depends on Catalog and Orders.
M6 hardens everything already built, so it follows M5; M7 deploys the hardened build.

## 5. RACI

Solo project: the Founder is Accountable for everything and is the sole decision-maker. The
`the_team/` hats are **Consulted**; the AI assistant is **Responsible** for producing
artifacts and code; the recruiter/client is **Informed** (reads the repo).

| Activity | Founder | Assistant | Hats | Reviewer |
|---|---|---|---|---|
| Plan / scope | A | R | C | I |
| Approve a stage gate | A/R | C | I | — |
| Write code + tests | A (review) | R | C | — |
| Commit (never push) | A (push) | R | — | I |
| QA scenarios / results | A | R (scenarios) | C | I |
| Deploy decision | A/R | C | C | I |

## 6. Definition of Done

- **Per increment:** see [`../WORKING-AGREEMENT.md`](../WORKING-AGREEMENT.md) §5.
- **Per milestone:** the milestone's exit criteria in §2 hold, and its increments are all committed and green.
- **v1:** the five evidence gates in [`../PLAN.md`](../PLAN.md) §2.

## 7. Change control

Any change to this roadmap follows `ADR-0002`: capture an ADR, append to
[`../CHANGE-LOG.md`](../CHANGE-LOG.md), and re-baseline [`../PLAN.md`](../PLAN.md). Scope
changes are the primary risk (`RISK-1`), so they are never made silently.

## 8. Risks

The full register is in [`RISK-REGISTER.md`](RISK-REGISTER.md).
