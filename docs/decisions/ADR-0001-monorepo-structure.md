# ADR-0001 — Monorepo structure

- **Status:** Accepted
- **Date:** 2026-10-09
- **Deciders:** Founder
- **Consulted hats:** senior_system_architect, senior_technical_lead

## Context

LYSHEIM ships two independently deployable applications — a Django API (`backend/`) and a
Next.js web app (`frontend/`) — and, unusually, the documentation set (`docs/`) is itself a
deliverable: a reviewer must be able to open one place and see the strategy, the
architecture, the code, and the history of how the plan changed.

Two constraints shape the choice:

1. **One author.** The coordination overhead of multiple repos buys nothing here.
2. **Reviewability.** A recruiter or client should be able to judge the project from a
   single clone.

## Options considered

1. **Two repositories** (one per application).
   - Pros: hard deployment boundary; independent history.
   - Cons: the reviewer needs two clones; a change that spans the API and its UI consumer
     cannot be one atomic commit; duplicated CI and docs.
2. **Single monorepo** (`backend/`, `frontend/`, `docs/`).
   - Pros: one clone; atomic cross-stack commits; shared root tooling config; docs sit next
     to the code they describe.
   - Cons: heavier repo; two toolchains (Python and Node) coexist, so CI must scope jobs
     per directory.
3. **Polyrepo with a shared contracts package.**
   - Pros: strongest service boundaries.
   - Cons: needs a private registry to publish the contracts package — pure overhead for a
     solo project.

## Decision

Use a **single monorepo** with three top-level directories: `backend/`, `frontend/`, and
`docs/`. The API contract is shared as an emitted OpenAPI schema (see a later ADR), not as a
published package.

## Consequences

- The reviewer clones once and can read everything.
- A change that spans API and UI lands as one coherent commit, which matches the
  small-increment working agreement.
- CI runs separate Python and Node jobs with path filters so an unrelated change does not
  rebuild everything.
- The repository grows faster than a single-app repo; acceptable at this scale.

## Reversibility

**Moderate.** Splitting into two repos later is mechanical (`git filter-repo`) but breaks
the atomic-commit property the project relies on. Cost of being wrong is low because the
decision is not load-bearing.

## References

- `docs/PLAN.md` §5 (Architecture at a glance)
- `docs/WORKING-AGREEMENT.md`
