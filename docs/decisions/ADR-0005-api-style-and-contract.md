# ADR-0005 — API style and contract

- **Status:** Accepted
- **Date:** 2026-10-09
- **Deciders:** Founder
- **Consulted hats:** senior_backend, senior_frontend_engineering, senior_system_architect

## Context

A Next.js frontend and a Django backend must agree on an interface. The contract has to be
typed enough that the client cannot silently drift from the server, and simple enough that a
solo developer can maintain it without code generation pipelines.

## Options considered

1. **REST + Django Ninja + OpenAPI.** Pros: Ninja is lightweight, async-friendly, and emits
   an OpenAPI 3 schema out of the box; client types can be generated from it; REST is
   universally understood by reviewers. Cons: REST granularity can cause over-fetching.
2. **REST + Django REST Framework.** Pros: ubiquitous, batteries included. Cons: heavier;
   serializer stack feels dated next to Ninja for a greenfield project.
3. **GraphQL.** Pros: flexible queries. Cons: significant tooling and caching complexity,
   and overkill for a storefront.
4. **A tRPC-style typed RPC.** Pros: end-to-end types. Cons: couples the client to a
   TypeScript server; our backend is Python.

## Decision

Use **REST over `/api/v1/` implemented with Django Ninja**, and treat the generated
**OpenAPI 3 schema as the shared contract**. Frontend client types are generated from that
schema so a server change that breaks the client is caught at build time.

## Consequences

- One schema document is the single source of truth for the API (`API.md` is its human view).
- Ninja's async support complements the async policy (`ADR-0006`).
- The reviewer sees a conventional, well-documented, versioned REST API.
- We accept occasional over-fetching; pagination and field selection are added only if a
  measured need appears (avoiding premature complexity).

## Reversibility

**Moderate.** Swapping the framework is contained within the API layer, but the emitted
contract's consumers would need regenerating. The REST *style* is effectively permanent.

## References

- `docs/03-architecture/API.md`
- `docs/03-architecture/ARCHITECTURE.md` §5
