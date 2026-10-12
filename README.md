# LYSHEIM

**Well-made home goods for everyday living.**

LYSHEIM is a home-goods e-commerce store — a portfolio project that models a real,
IKEA-inspired retail business and then builds a production-grade slice of it. It exists to
demonstrate, to a recruiter or a freelance client, both **commercial thinking** and **senior
engineering execution**.

> **Status: in progress.** Phase 1 is deployed: the API, the database and the web app are live, and the
> walking skeleton serves the catalogue. What is built and what is next is in
> [`docs/04-delivery/ROADMAP.md`](docs/04-delivery/ROADMAP.md).

## Live demo

| | |
| --- | --- |
| **Web** | <https://ecommerce-project-five-psi.vercel.app> |
| **API** | <https://lysheim-api.onrender.com> (`/healthz`, `/api/v1/products`) |

Working today: browsing the catalogue — 7 categories and 46 products, read from the live API, which
reads Postgres. Registration, sign-in and the account screen are built and deployed as well. Checkout
is not built yet.

**The first visit is slow, and that is the trade rather than a fault.** Both hosts are on free tiers
that sleep when idle, so the first request to a route after a quiet spell can take tens of seconds.
Measured 2026-10-12: the first page load took 48s, the next 2s; a single route 28s on its own first
hit; the API 1s once awake. [`ADR-0011`](docs/decisions/ADR-0011-deployment-stack.md) accepts that as
the price of the free tier and names a keep-alive ping as the mitigation, which is not built yet. One
patient load, and everything after it is quick.

## Stack

- **Backend:** Python · Django 6 · Django Ninja · PostgreSQL · `uv` · `ruff` · `basedpyright`
- **Frontend:** Next.js (App Router) · TypeScript · `pnpm` · ESLint · Prettier
- **Delivery:** Docker Compose (local) · GitHub Actions (CI) · Render · Vercel · Supabase

## Documentation

The documentation is a first-class deliverable. Start here:

- [`docs/PLAN.md`](docs/PLAN.md) — the living master plan
- [`docs/01-business/STRATEGY.md`](docs/01-business/STRATEGY.md) — market, model, positioning
- [`docs/CHANGE-LOG.md`](docs/CHANGE-LOG.md) — how the plan has changed
- [`docs/decisions/`](docs/decisions/) — architecture decision records
- [`docs/WORKING-AGREEMENT.md`](docs/WORKING-AGREEMENT.md) — how the work is executed

## Repository layout

```
backend/     Django + Ninja API
frontend/    Next.js web app
docs/        planning, architecture, delivery, and decision records
```
