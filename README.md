# LYSHEIM

**Well-made home goods for everyday living.**

LYSHEIM is a home-goods e-commerce store — a portfolio project that models a real,
IKEA-inspired retail business and then builds a production-grade slice of it. It exists to
demonstrate, to a recruiter or a freelance client, both **commercial thinking** and **senior
engineering execution**.

> **Status: planning.** The project is in its planning phase. Strategy and architecture are
> baselined before application code is written. See [`docs/PLAN.md`](docs/PLAN.md).

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
