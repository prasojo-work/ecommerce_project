# ADR-0001: Monorepo with decoupled backend and frontend

- **Status:** Accepted
- **Date:** 2026-10-04
- **Deciders:** Founder
- **Related:** `ADR-0002`, `ADR-0005`

## Context

The project has two applications — a Django API and a Next.js web client — that communicate over HTTP. The author is solo, and the audience (recruiters/clients) will read the repository. We need a layout that is easy to navigate, easy to keep in sync, and easy to demonstrate, on a free hosting tier.

## Options considered

1. **Monorepo** (`backend/` + `frontend/` + `docs/`) — one git repository, one history, one place to look. Deploying still targets separate hosts, so the coupling is only at the source level.
2. **Two repositories** — clean separation, independent deploy lifecycles, but two things to clone, two issue trackers, and harder to view as one story.
3. **Single Django app serving templates** — simplest to run, but abandons the chosen decoupled stack and the frontend portfolio signal.

## Decision

Use a **monorepo** with `backend/` and `frontend/` as independent applications and `docs/` for planning artifacts. The two apps share nothing at the source level except the API contract (generated from the API's OpenAPI schema).

## Consequences

- **Positive:** one repository to show a reviewer; atomic commits that span API + client; shared docs; trivially demonstrable.
- **Negative / costs:** separate deploy pipelines still needed (Vercel vs Render); a monorepo can hide the fact the apps are deployable independently if not documented — hence this ADR.
- **Follow-ups:** CI must scope jobs per app.

## Reversibility

**High.** Splitting into two repos later is a clean, mechanical operation. The API contract already decouples them.
