# ADR-0006 — Async and background tasks (Django 6)

- **Status:** Accepted
- **Date:** 2026-10-09
- **Deciders:** Founder
- **Consulted hats:** senior_backend, senior_system_architect, senior_cloud_engineer

## Context

Django 6 (released December 2025) ships a built-in **Tasks framework** (`@task` decorator,
enqueue, result handling) and deeper async support, and requires Python 3.12+. The founder
asked that async be used *where appropriate*. We need a policy so async is used for real
benefit and not as decoration, and so background work (order-confirmation email, Phase 2
event emission) does not block HTTP requests.

## Options considered

1. **Celery / RQ.** Pros: powerful, familiar. Cons: an extra broker (Redis) and operational
   surface for a project whose only background jobs are lightweight.
2. **Synchronous only.** Pros: simplest. Cons: blocks requests on I/O; ignores a headline
   capability of the chosen framework version.
3. **Django 6 built-in Tasks + ASGI, used pragmatically.** Pros: no extra infrastructure;
   demonstrates the modern framework; clear win for off-request work. Cons: newer, smaller
   ecosystem than Celery.

## Decision

- Serve the API over **ASGI** (Uvicorn) in development and production.
- Use **`async def` handlers** for **I/O-bound** endpoints (e.g. the mock payment gateway
  call) and the **async ORM** (`acreate`, `aget`, `async for`) where it removes real
  blocking. Keep ordinary synchronous code where async adds no value.
- Use the **built-in Tasks framework** for background work: order-confirmation email
  (mocked transport) and Phase 2 event emission. **Do not add Celery** for v1.

## Consequences

- No broker to run or pay for; fewer moving parts on free tiers.
- A worker process is needed to execute tasks in production (a Render background worker).
- The codebase mixes sync and async intentionally; a short convention note is added to the
  backend README so contributors know when to choose which.
- Uses a genuinely modern Django capability, which is itself portfolio value.

## Reversibility

**Moderate.** Task functions are isolated, so introducing Celery later would be mechanical
if volume ever demanded it. The ASGI choice is cheaply reversible.

## References

- `docs/PLAN.md` §5 (Async policy)
- `docs/03-architecture/ARCHITECTURE.md` §10
