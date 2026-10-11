# Delivery Roadmap — LYSHEIM

> Consulted hats: **Senior Technical Lead** and **Senior Technical Project Manager**. Owner:
> Founder. Inputs: [`../PLAN.md`](../PLAN.md), [`../02-product/SCOPE.md`](../02-product/SCOPE.md),
> [`../03-architecture/ARCHITECTURE.md`](../03-architecture/ARCHITECTURE.md).
> Execution rules live in [`../WORKING-AGREEMENT.md`](../WORKING-AGREEMENT.md).
> Cadence: continuous increments, a compact change-log entry per increment, and a milestone
> retrospective at each gate
> ([`../decisions/ADR-0015-continuous-increments.md`](../decisions/ADR-0015-continuous-increments.md),
> [`../decisions/ADR-0016-lean-increment-ceremony.md`](../decisions/ADR-0016-lean-increment-ceremony.md)).

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
| M0 | Foundations | Both apps boot, gates wired, CI green | `docker compose up` runs API + web; CI passes | `[x]` |
| M1 | Catalog & browse | Products visible and navigable | Browse → PDP works with seeded data | `[x]` |
| M2 | Accounts & auth | Register/login works; the app is live | JWT flow + refresh exercised by tests; a public URL serves the catalog and auth | `[~]` |
| M3 | Cart | Server-side cart for guests + users | Add/update/remove + merge on login | `[ ]` |
| M4 | Checkout & orders | Mock purchase end to end | Order created, paid, history shown | `[ ]` |
| M5 | Operator console | Catalog/stock/orders manageable | Admin manages products + order status | `[ ]` |
| M6 | Hardening | Quality evidence produced | a11y/perf/security reports committed | `[ ]` |
| M7 | Launch | Public demo hardened and finalised | Live URL passes a smoke journey; README published | `[ ]` |
| M8 | Data track (Phase 2) | Analytics on real events | Funnel dashboard built on events | `[ ]` |

## 3. Milestone detail

### M0 — Foundations

- [x] `M0.1` Backend scaffold: `uv` project, Django 6, Django Ninja, settings split by env.
- [x] `M0.2` Frontend scaffold: Next.js (App Router, TypeScript strict), `pnpm`, design tokens → `globals.css`.
- [x] `M0.3` Root tooling: `ruff` + `basedpyright` (standard) config; ESLint + Prettier; `.editorconfig`.
- [x] `M0.4` Test harness: `pytest` (backend), `vitest` (frontend), one trivial test each.
- [x] `M0.5` `/healthz` endpoint + JSON logging + request-id middleware.
- [x] `M0.6` `.env.example`, `django-environ` wiring, secrets excluded from git.
- [x] `M0.7` `compose.yml` (Postgres + API + web) with a one-command start.
- [x] `M0.8` `seed` management command skeleton (idempotent, `--reset`).
- [x] `M0.9` GitHub Actions CI: path-filtered jobs for backend and frontend gates.
- [x] `M0.10` Tailwind CSS adopted; tokens declared in `@theme` (revises `M0.2`, `ADR-0013`).

### M1 — Catalog & browse

- [x] `M1.1` Catalog models + migrations (`Category`, `Product`, `ProductVariant`, `ProductImage`, `ImageCredit`).
- [x] `M1.2` Seed catalog: categories, products, variants, stock; curated images + credits vendored from `some_source/` (7 categories, 46 products).
- [x] `M1.3` Catalog read API (`/categories`, `/products`, `/products/{slug}`) + OpenAPI, with pagination, filters, and the error envelope.
- [x] `M1.4` Frontend API types generated from the committed OpenAPI snapshot (`frontend/openapi.json`), with a drift check in `Backend CI`.
- [x] `M1.5` Catalog listing page (grid, pagination, skeletons, empty state), partial-prerendered with the listing streamed behind a Suspense boundary.
- [x] `M1.6` Product detail page (gallery, price, availability, add-to-cart placeholder, per-product metadata); catalog cards now link to it.
- [x] `M1.7` Search, filter, and sort with shareable URL state — `?q=`, `?category=`, `?min_price=`, `?max_price=`, `?sort=`, `?page=`, carried through paging.
- [x] `M1.8` Home page (hero + featured), partial-prerendered: text hero in the shell, featured row streamed behind a Suspense boundary.
- [x] `M1.9` `/pages/credits` attribution page (`US-6.1`), reading a new public `/api/v1/credits` endpoint: every shipped image credited from the database, licence codes linked to their Creative Commons deeds.

### M2 — Accounts & auth

- [x] `M2.1` Custom `User` model + `Address` model + migrations; `django.contrib.auth` installed and `AUTH_USER_MODEL` swapped while the database still had no `auth_user` table.
- [x] `M2.2` Auth endpoints: register, login, refresh, logout, me (`ADR-0009`) — access token in the body, refresh token only as an httpOnly cookie scoped to the auth routes, with rotation and reuse detection.
- [x] `M2.3` Rate limiting on every auth endpoint (`US-2.2`, `NFR-3`) — keyed on the client rather than the account, so a limiter cannot be turned into a way to lock someone out of their own sign-in — with the limits themselves in settings, plus `ADR-0009`'s origin guard on `/auth/refresh`, which answers `403` before reading the cookie.
- [x] `M2.4` Frontend session: the access token in memory only, with one shared in-flight refresh so two concurrent calls cannot trip `ADR-0009`'s reuse detection and sign the customer out of everything; a three-state session (`restoring`/`authenticated`/`anonymous`) so a reload never flashes "signed out"; and the CORS configuration the browser needs, which had been missing entirely.
- [x] `M2.5` Login / register pages with validation.
- [~] `M2.6` Profile + addresses CRUD (API and UI) — API half done (`PATCH /auth/me`, the `/addresses`
  routes); the profile and address UI is the other half.
- [ ] `M2.7` **Deploy the walking skeleton.** A public URL that serves the catalog and auth: the
  backend `Dockerfile`, Render (web), Supabase, and Vercel, migrations and seed on the demo
  database, `CORS_ALLOWED_ORIGINS` set for the real origins, and a smoke journey over the public
  URL. Pulls `M7`'s configuration work forward to the first point where there is something worth
  showing, so a live URL exists halfway through Phase 1.

### M3 — Cart

- [ ] `M3.1` `Cart` / `CartItem` models and API — get, add, update, remove, with server-side stock
  validation and the signed guest cookie resolution (`ADR-0008`). *(merges the old `M3.1` + `M3.2`)*
- [ ] `M3.2` Guest-cart merge on login.
- [ ] `M3.3` Cart UI: line items, quantity stepper, totals, empty state.

### M4 — Checkout & orders

- [ ] `M4.1` `Order` / `OrderItem` / `OrderEvent` models; guarded status transitions.
- [ ] `M4.2` `/checkout/quote` (shipping options + totals).
- [ ] `M4.3` Idempotent order creation (`Idempotency-Key`) with stock decrement, plus the
  `PaymentGateway` port and its mock adapter with confirm/fail endpoints (`ADR-0010`).
  *(merges the old `M4.3` + `M4.4`)*
- [ ] `M4.4` Order-confirmation email via the Tasks framework (mocked transport).
- [ ] `M4.5` Checkout UI: address → shipping → payment → confirmation.
- [ ] `M4.6` Order history and order-detail pages.

### M5 — Operator console

- [ ] `M5.1` Django admin for the catalog and orders — list filters, search, inline images, guarded
  status transitions, and the audit visible. *(merges the old `M5.1` + `M5.2`)*
- [ ] `M5.2` Operator runbook entry (create an `is_staff` operator; day-to-day actions).

### M6 — Hardening

- [ ] `M6.1` Coverage push on the domain/service layer (≥ 80%) plus tests for edge cases.
- [ ] `M6.2` Accessibility (axe on key routes) **and** performance (LCP budget, caching, image
  optimisation) pass → one combined report. *(merges the old `M6.2` + `M6.3`)*
- [ ] `M6.3` Security hardening (CSP, headers, throttles, secret guard, dependency audit) and the
  end-to-end error-envelope + request-id verification → `SECURITY-REVIEW.md`.
  *(merges the old `M6.4` + `M6.5`)*

### M7 — Launch

`M7` is thin by design: `M2.7` already stood up the deploy, so this is the hardened, final one.

- [ ] `M7.1` Production deploy — Render web **and** worker, Supabase, Vercel; run migrations and
  seed the demo database.
- [ ] `M7.2` Production smoke journey + keep-alive ping; finalise the runbook.
- [ ] `M7.3` README with screenshots, architecture diagram, and the live URL.

### M8 — Data track (Phase 2, deferred)

- [ ] `M8.x` Per `ARCHITECTURE.md` §9 and `_working/TODO_data-engineer.md`; ADRs written at the start of Phase 2.

## 4. Sequencing & dependencies

`M0 → M1 → M2 → M3 → M4 → M5 → M6 → M7`, then `M8`. Cart (M3) depends on Catalog (M1) and
Identity (M2); Checkout (M4) depends on Cart; Operator (M5) depends on Catalog and Orders.
`M2.7` deploys the walking skeleton as soon as auth works, so the catalog and sign-in are publicly
reachable from the middle of `M2` and every later increment lands on a live system. M6 hardens
everything already built, so it follows M5; M7 finalises that hardened build on the public URL.

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
- **Per milestone:** the milestone's exit criteria in §2 hold, its increments are all committed and green, and a short retrospective is appended to `CHANGE-LOG.md`.
- **v1:** the five evidence gates in [`../PLAN.md`](../PLAN.md) §2.

## 7. Change control

Any change to this roadmap follows `ADR-0002`: capture an ADR, append to
[`../CHANGE-LOG.md`](../CHANGE-LOG.md), and re-baseline [`../PLAN.md`](../PLAN.md). Scope
changes are the primary risk (`RISK-1`), so they are never made silently.

## 8. Risks

The full register is in [`RISK-REGISTER.md`](RISK-REGISTER.md).
