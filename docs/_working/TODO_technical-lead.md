# TODO — Technical Lead (raw working file)

> Raw output of the `senior_technical_lead` hat for LYSHEIM, committed for transparency.
> Curated sources: [`../04-delivery/ROADMAP.md`](../04-delivery/ROADMAP.md),
> [`../WORKING-AGREEMENT.md`](../WORKING-AGREEMENT.md).

## Context

- Team: one founder + an AI assistant. The lead's job is technical direction, quality, and
  process — not people management.
- Stage: delivery planning (Stage 4). Engineering standards were set in `ADR-0004` and
  `WORKING-AGREEMENT.md`.

## Technical Direction

- [ ] **TL-1.1 [Direction set]** — stack and architecture fixed in `ADR-0001..0012`; no
  relitigating settled decisions (new change = new ADR).
- [ ] **TL-1.2 [Increment sizing]** — every increment is small, demoable, gated, and tested
  (`ROADMAP.md` §3). A milestone is a reviewer-visible capability.
- [ ] **TL-1.3 [Trade-off calls]** — prefer boring, proven technology; async used only where
  it pays (`ADR-0006`); Django admin over a bespoke console for v1 (`ADR-0007`).

## Code Quality

- [ ] **TL-2.1 [Gates]** — `ruff` + `basedpyright` standard (backend); ESLint + `tsc` strict
  (frontend); tests per increment.
- [ ] **TL-2.2 [Review standard]** — defined fully in Stage 5; interim rule: no increment
  merges (commits) red, no untested behaviour.
- [ ] **TL-2.3 [Technical debt]** — debt is logged as `RISK-*` or a roadmap increment, never
  left implicit.

## Delivery & Process

- [ ] **TL-3.1 [Definition of Done]** — codified per increment and per milestone
  (`ROADMAP.md` §6).
- [ ] **TL-3.2 [Change control]** — ADR → change log → re-baseline (`ADR-0002`); protects the
  finish line (`RISK-1`, `RISK-4`).
- [ ] **TL-3.3 [Runbook discipline]** — every increment states how to run itself
  (`RUNBOOK.md`).
- [ ] **TL-3.4 [Budgets]** — performance, accessibility, and cost budgets are release
  criteria, not aspirations (`SCOPE.md` `NFR-1/2/8`).

## Mentor Notes (self)

- [ ] **TL-4.1** Keep vertical slices thin so the demo is always presentable.
- [ ] **TL-4.2** Write the reviewer-facing doc while the decision is fresh.

## Commands

- N/A (planning/leadership stage).
