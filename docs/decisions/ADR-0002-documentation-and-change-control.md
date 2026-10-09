# ADR-0002 — Documentation and change control

- **Status:** Accepted
- **Date:** 2026-10-09
- **Deciders:** Founder
- **Consulted hats:** senior_technical_project_manager, senior_multi_agent_orchestrator

## Context

The primary reviewer question is not "does it work" but "can this person be trusted with a
moving project". A portfolio that only shows a finished website cannot answer that. We need
artifacts that make the *thinking* and the *adaptation* visible: what the plan was, why
decisions were taken, and how the plan changed mid-flight.

The previous iteration of this repository used a documentation convention that worked well;
we reuse it deliberately (see `CHANGE-LOG.md` for the reset context).

## Options considered

1. **README-only.** Pros: minimal. Cons: no history of change, no decision record.
2. **Living plan + append-only change log + ADRs** (the prior convention).
   - Pros: current truth lives in one place (`PLAN.md`); history is immutable
     (`CHANGE-LOG.md` + `decisions/`); decisions are not silently relitigated.
   - Cons: needs discipline; docs must be maintained, not written once.
3. **Wiki or external tool.** Pros: nicer UI. Cons: lives outside the repo, invisible to a
   reviewer who only opens GitHub, and drifts from the code.

## Decision

Adopt three document classes, reused from the prior iteration:

- **`PLAN.md`** — *living*. Edited in place to always reflect the current agreed plan.
- **`CHANGE-LOG.md`** — *append-only*. Every change to the plan is recorded with date,
  rationale, and links.
- **`decisions/ADR-NNNN-*.md`** — *append-only*. One file per significant decision; never
  edited after acceptance (only `status` may change).

Every trackable item carries a stable ID prefix (`GOAL-`, `EPIC-`, `US-`, `NFR-`, `SYS-`,
`DATA-`, `PLAN-`, `RISK-`, `STRAT-`, `ADR-`). IDs are never reused or renumbered; retired
items are marked `[DROPPED]` and kept for history.

**Change procedure.** When the plan moves: (1) capture the decision as an ADR, (2) append
the delta and rationale to `CHANGE-LOG.md`, (3) re-baseline `PLAN.md` and bump its version.

## Consequences

- The reviewer sees both the current plan and the trail of change.
- Re-planning costs a little time (ADR + changelog + re-baseline) — this is a feature: it
  discourages thrash.
- Documentation is in scope for every increment, not an afterthought.

## Reversibility

**Cheap.** This is a process convention; it can be changed or abandoned at any time.

## References

- `docs/README.md` (conventions)
- `docs/PLAN.md` §8 (Governance)
