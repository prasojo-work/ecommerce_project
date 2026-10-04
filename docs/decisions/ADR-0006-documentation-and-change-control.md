# ADR-0006: Documentation and change-control model

- **Status:** Accepted
- **Date:** 2026-10-04
- **Deciders:** Founder
- **Related:** all ADRs

## Context

The project is a portfolio artifact whose value depends on *visible thinking*, and it deliberately simulates a start-up where the plan changes mid-flight. The author wants a record of both the plan and how the plan evolved. The `the_team/` role prompts each mandate writing a single `TODO_<role>.md` file — a constraint that, taken literally, would scatter the plan across a dozen files and fight with a coherent narrative.

## Options considered

1. **Literal role outputs** — one `TODO_<role>.md` per role. Faithful to the prompts, but fragmented and confusing to a reviewer.
2. **Consolidated docs tree with roles as thinking hats** — the role prompts are *consulted* during planning, and their output is merged into a single structured `docs/` tree. Chosen.
3. **No docs** — fastest, but destroys the point of the artifact.

## Decision

Adopt a **consolidated `docs/` tree** with three interacting artifacts:

- **`PLAN.md`** — the *living* plan, always current, versioned.
- **`CHANGE-LOG.md`** — an *append-only* record of every change to the plan (what, why, impact, linked ADR).
- **`decisions/ADR-*.md`** — one *append-only* record per significant decision.

The `the_team/` role prompts are used as **consulting lenses**, not as file-writing agents. Every planning doc names the hat(s) consulted at its top.

The change flow: **raise → decide (ADR) → log (CHANGE-LOG) → re-baseline (PLAN)**. Change is welcomed; *undocumented* drift is not.

## Consequences

- **Positive:** a single, coherent, reviewable narrative; a legible history of change; the simulated-start-up dynamic is captured honestly; docs double as a demonstration of change-management discipline.
- **Negative / costs:** the literal "one TODO file per role" rule of the prompts is intentionally overridden — this ADR is the explicit justification; discipline is required to keep `PLAN.md` current.
- **Follow-ups:** re-baseline `PLAN.md` and append to `CHANGE-LOG.md` at each milestone boundary.

## Reversibility

**High.** The documentation structure is cheap to change; it is not load-bearing for the code.
