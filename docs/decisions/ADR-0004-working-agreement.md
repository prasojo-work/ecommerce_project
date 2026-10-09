# ADR-0004 — Working agreement (solo founder + AI assistant)

- **Status:** Accepted
- **Date:** 2026-10-09
- **Deciders:** Founder
- **Consulted hats:** senior_technical_lead, senior_multi_agent_orchestrator

## Context

The project is executed by one founder directing an AI assistant. Without an explicit
agreement, increments blur, quality gates get skipped, and the history becomes unreadable.
The founder specified a delivery rhythm; the assistant added quality gates and governance.
This ADR records the merged agreement so it is authoritative and stable.

## Options considered

1. **Ad hoc.** Pros: none. Cons: drift, skipped tests, unclear history.
2. **Explicit written agreement** (chosen): small increments; format and type gates; unit
   tests per increment; local commit without push; scenario-based QA by a separate tester
   agent; run instructions after each increment.

## Decision

Adopt the working agreement in `docs/WORKING-AGREEMENT.md`. In summary:

1. Every change is a small, demoable increment.
2. Each increment passes formatting and type checks before it is committed.
3. Each increment ships unit tests (mock/fixture data) that pass.
4. After tests pass: `git add` + `git commit`; **never `git push`** — the founder pushes.
5. When UI exists, the assistant writes QA scenarios (normal + edge cases + expected
   result); a separate **tester agent** executes them in another session. Scenarios are the
   assistant's and mutable; tester **results are immutable** to the assistant (a stale
   result may be deleted, never edited).
6. After each increment the assistant states how to run it for manual verification.
7. The database is seeded via an idempotent management command using dummy data.
8. All external connections come from configuration (environment variables), so deploying
   changes configuration only, never code.

**Strictness decisions:** `basedpyright` in *standard* mode (not `strict`); ruff `ANN` on
the service/domain layer only; TypeScript `strict: true`; ESLint *recommended* (not
type-checked) for v1.

## Consequences

- History stays legible and every increment is independently reviewable.
- The founder controls what reaches GitHub; nothing is published accidentally.
- QA has provenance: nobody can silently rewrite a test result.
- Slightly more ceremony per increment; accepted deliberately.

## Reversibility

**Cheap.** It is a process agreement and can be amended by a new ADR.

## References

- `docs/WORKING-AGREEMENT.md`
