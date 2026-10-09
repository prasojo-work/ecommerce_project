# TODO — Backend (raw working file)

> Raw output of the `senior_backend` hat for LYSHEIM. Curated source:
> [`../03-architecture/ARCHITECTURE.md`](../03-architecture/ARCHITECTURE.md) and
> [`DATA-MODEL.md`](../03-architecture/DATA-MODEL.md).

## Context

- Stack: Python 3.12+, Django 6, Django Ninja, PostgreSQL, `uv`, `ruff`, `basedpyright`.
- Scope: the REST API, domain model, auth, cart, checkout, and the admin console.

## Design Items

- [ ] **BE-1.1 [Project layout]** — apps `core/accounts/catalog/cart/orders/payments`;
  settings by environment; no secrets in code.
- [ ] **BE-1.2 [Domain models]** — implement per `DATA-MODEL.md`; money as integer cents;
  status transitions guarded.
- [ ] **BE-1.3 [API layer]** — Ninja routers per context; OpenAPI emitted; error envelope +
  request-id middleware.
- [ ] **BE-1.4 [Auth]** — JWT access (memory) + refresh (httpOnly cookie); rate limiting;
  refresh CSRF/origin guard (`ADR-0009`).
- [ ] **BE-1.5 [Cart]** — cookie-keyed guest carts, merge on login (`ADR-0008`).
- [ ] **BE-1.6 [Checkout & orders]** — idempotent order creation; stock decrement; snapshots.
- [ ] **BE-1.7 [Payments]** — `PaymentGateway` port + mock adapter (`ADR-0010`).
- [ ] **BE-1.8 [Async & tasks]** — ASGI; `async def` where I/O-bound; Tasks for the
  confirmation email (`ADR-0006`).
- [ ] **BE-1.9 [Observability]** — JSON logs, request ids, `/healthz`.
- [ ] **BE-1.10 [Operability]** — Dockerfile, `.env.example`, `seed` management command.

## Quality Gates

- [ ] `ruff` + `ruff format` clean. · [ ] `basedpyright` standard clean.
- [ ] `pytest` green; domain/service coverage ≥ 80%.

## Commands

- Dev: `uv run uvicorn config.asgi:application --reload`
- Checks: `uv run ruff check . && uv run basedpyright && uv run pytest`
