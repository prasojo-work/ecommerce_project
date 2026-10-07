# NORDVIK

**NORDVIK** is a home-goods e-commerce store — a portfolio project that models a real,
IKEA-inspired retail business and then builds a production-grade slice of it.

- **Backend:** Django 6 + Django Ninja + PostgreSQL (`uv`, `ruff`, `basedpyright`)
- **Frontend:** Next.js + TypeScript (`pnpm`)
- **Docs:** see [`docs/`](docs/)

## Repository layout

\`\`\`
.
├── backend/      Django + Ninja API
├── frontend/     Next.js web app
└── docs/         Planning, architecture, and decisions
\`\`\`

## Documentation

The full plan, business strategy, architecture, and decision records live in
[`docs/`](docs/). Start at [`docs/README.md`](docs/README.md).

## Operator console

The store operator manages the catalog, inventory and orders through Django's admin at
`/admin/`. Create the account once:

```sh
cd backend && uv run python manage.py createsuperuser
```

Orders are read-only except for guarded fulfilment actions (processing → shipped → completed, or
cancel, which returns the reserved stock). Catalogue products, variants and stock levels are
editable, with a stock-level filter for what needs reordering. See
[`ADR-0011`](docs/decisions/ADR-0011-operator-console.md).

## Status

Feature-complete through **M5 (admin)**. Next: **M6 (hardening)** — the NFR pass, including the
deferred [end-to-end suite](docs/04-delivery/E2E-TEST-PLAN.md) — then **M7 (deploy)**.