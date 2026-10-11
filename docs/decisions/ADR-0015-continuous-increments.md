# ADR-0015 — Continuous increments (amends the working agreement)

- **Status:** Accepted
- **Date:** 2026-10-11
- **Deciders:** Founder
- **Consulted hats:** senior_technical_lead, senior_multi_agent_orchestrator

## Context

`ADR-0004` settled a working agreement in which every change is a small, demoable increment that
passes the gates and ships tests before the next one begins. Read together with the founder's
original instruction, it was also being applied as an *interaction* rule: after each increment the
assistant stopped and waited to be told to continue.

That costs a round trip per increment and gets slower as the increments get finer, which is backwards
— the smaller the slice, the more overhead the pause adds. The founder revised it: keep slicing the
work small, but keep going, and stop only when there is genuinely something to decide.

## Options considered

1. **One increment, then wait** (the previous reading). Pros: the founder sees every step before
   anything is built on it. Cons: a round trip per increment, and most of those waits decide nothing —
   the review value is already carried by the commit, the gates, and the QA file.
2. **Continuous increments, stop only for a decision** (chosen). Pros: no dead time, and the stops
   that remain are the ones that actually need a person. Cons: a run of increments can travel further
   before the founder reads it — mitigated because each increment is its own commit, and the tree is
   reviewable at any point precisely because nothing has been pushed.

## Decision

`docs/WORKING-AGREEMENT.md` §1 rule 1 stands unchanged in substance — every commit is still one
small, demoable step that passes the gates and ships tests — but the assistant **does not pause
between increments**.

It stops only when the founder has to decide something:

- a product or UX choice, or a trade-off with no clearly better answer;
- a scope change (the process `ADR-0002` sets out);
- a credential, account, or external service the founder must supply;
- a deploy or publish step, which the RACI in `ROADMAP.md` §5 reserves for the founder.

Reporting progress is not a reason to stop. It happens in the commit, and in the notes that
`ADR-0004` rule 6 already requires for every increment.

## Consequences

- Fewer round trips for the same review surface.
- The founder reviews a run of commits rather than a single one, which makes "commit locally, never
  push" (`ADR-0004` rule 4) more load-bearing than before — nothing becomes public without a decision.
- Nothing else in `ADR-0004` changes: quality gates, unit tests per increment, QA scenario
  provenance, and run instructions all still apply to each increment.

## Reversibility

**Cheap.** It is a process agreement, amended the same way it was made.

## References

- `docs/WORKING-AGREEMENT.md`
- `docs/decisions/ADR-0004-working-agreement.md`
- `docs/04-delivery/ROADMAP.md` §5 (RACI)
