# ADR-0002: Django Ninja (not DRF) as the API layer

- **Status:** Accepted
- **Date:** 2026-10-04
- **Deciders:** Founder
- **Related:** `ADR-0001`, `ADR-0003`

## Context

The backend exposes a REST API for a decoupled Next.js client. Two mature options dominate in Django: Django REST Framework (DRF) and Django Ninja. The author values type safety (`basedpyright`) and modern Python, and also cares about signalling the right skills to reviewers, where DRF is the more common keyword.

## Options considered

1. **Django REST Framework (DRF)** — the industry-standard, vast ecosystem, most familiar to hiring managers. But it is serializer-heavy, class-based, and gives weaker static typing without extra tooling.
2. **Django Ninja** — FastAPI-style, Pydantic v2 schemas, async-capable, automatic OpenAPI, and strong typing that fits `basedpyright`. Smaller ecosystem and fewer job-posting mentions.
3. **Plain Django views** — minimal deps, but we would rebuild serialization/validation/documentation poorly.

## Decision

Use **Django Ninja**. It aligns with the author's typing discipline, produces an OpenAPI schema the frontend can consume directly, and results in less boilerplate. We accept that DRF is the more "expected" keyword and mitigate this in the documentation (this ADR) and by noting transferable concepts.

## Consequences

- **Positive:** typed request/response schemas; auto-generated docs; less code; pleasant developer experience.
- **Negative / costs:** smaller community; some third-party packages assume DRF (e.g. auth helpers) and need adaptation; a reviewer specifically searching for "DRF" will not find it.
- **Follow-ups:** JWT auth must be wired for Ninja (see `ADR-0003`).

## Reversibility

**Medium.** Swapping the API layer would mean rewriting routers/schemas, but the domain and data layers are untouched, so the blast radius is contained to the presentation layer.
