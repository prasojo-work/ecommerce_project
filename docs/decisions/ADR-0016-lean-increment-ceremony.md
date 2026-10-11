# ADR-0016 — Lean increment ceremony (amends the change-log and ADR thresholds)

- **Status:** Accepted
- **Date:** 2026-10-12
- **Deciders:** Founder
- **Consulted hats:** senior_technical_lead, senior_technical_project_manager, senior_multi_agent_orchestrator

## Context

`ADR-0002` sets three document classes and a change procedure; `ADR-0004` adds per-increment
duties. Applied literally, every increment also produced a ~500-word `CHANGE-LOG.md` entry with
"Decisions taken" and "Impact" sections, and any micro-decision drifted toward its own ADR. The cost
scales linearly with the number of increments — Phase 1 has ~50 — while the anti-slop value of that
prose is small. The defects this project has actually caught came from the gates and from running the
code, not from the retrospective narrative: a throttle whose rate was read at import time, a refresh
that raised instead of returning its `401`, a mocked test that never overlapped, and an `API.md`
field name that only asking the running API exposed.

`ADR-0015` removed the pause between increments. This ADR removes the *prose tax* on top of it,
without weakening the gates that do the real work.

## Options considered

1. **Keep the current ceremony.** Pros: maximum narrative per step. Cons: linear cost for little
   anti-slop value, and a change log that becomes unreadable at a glance.
2. **Drop the change log.** Pros: cheapest. Cons: loses the history of change that `ADR-0002` exists
   to give a reviewer, and re-opens re-litigation of settled decisions.
3. **Tiered ceremony** (chosen): a terse per-increment log line, long-form rationale once per
   milestone, and an ADR only for decisions that are expensive or awkward to reverse.

## Decision

1. **Per increment, the `CHANGE-LOG.md` entry is terse** — one compact block: the increment ID and
   name, what changed (bullets of files), the gates that passed with test counts, and any decision
   worth a single line. No "Decisions taken" or "Impact" essays per increment.
2. **The long-form rationale is written once per milestone**, as a short retrospective appended to
   `CHANGE-LOG.md` at the milestone gate: the decisions taken across the milestone, what the code
   proved, and the evidence. Prose belongs here, because a milestone is the unit a reviewer reads.
3. **An ADR is required only for a decision that is expensive or awkward to reverse** — the data
   model, the auth/token model, the stack, an external contract, or anything with a migration or a
   public interface. Micro-decisions are recorded in the commit message or as one line in the
   milestone retrospective.
4. **The `ADR-0002` change procedure (ADR + change-log + re-baseline `PLAN.md`) applies to
   *plan-level* changes**, not to every increment. An increment that simply follows the plan needs
   only its commit and its terse log line.
5. **The gates are unchanged and remain the load-bearing anti-slop** — `ruff`, `basedpyright`,
   ESLint, `tsc`, the test suites, and the pre-commit hook. Nothing here relaxes them.
6. **QA provenance is unchanged** (`ADR-0004` §3): scenarios are the assistant's and mutable, tester
   results are immutable. The tester agent runs **per feature or milestone**, not per
   micro-increment.

## Consequences

- The change log becomes scannable — one screen per milestone instead of five — which makes it more
  useful to the reviewer `ADR-0002` was written for.
- The pace set by `ADR-0015` is no longer throttled by writing.
- The commit history is the primary, granular trace; the milestone retrospective is the interpreted
  one. Both remain; only the duplication between them is removed.
- Risk: a run of increments is described in less detail until its milestone closes. Mitigated because
  each increment is still its own gated, tested commit, reviewable at any time (`ADR-0015`).

## Reversibility

**Cheap.** It is a documentation-cadence agreement and is amended the same way it was made.

## References

- `docs/WORKING-AGREEMENT.md`
- `docs/decisions/ADR-0002-documentation-and-change-control.md`
- `docs/decisions/ADR-0004-working-agreement.md`
- `docs/decisions/ADR-0015-continuous-increments.md`
- `docs/04-delivery/ROADMAP.md`
- `docs/06-quality/CODE-REVIEW-STANDARD.md`
