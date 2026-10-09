# TODO — Multi-Agent Orchestrator (raw working file)

> Raw output of the `senior_multi_agent_orchestrator` hat for LYSHEIM, committed for
> transparency. The curated, reviewer-facing version is
> [`../06-quality/AGENT-TOPOLOGY.md`](../06-quality/AGENT-TOPOLOGY.md).

## Context

- "Agent system" = the founder (human orchestrator) + the assistant (builder) + a tester agent
  + the `the_team/` specialist hats.
- Goal: make the workflow deterministic, auditable, and safe, with no hidden state.

## Design Items

- [x] **TASK-1.1 [Topology]** — hierarchical, human-in-the-loop; one writer; independent
  verifier. Deliverable: `AGENT-TOPOLOGY.md` §1.
- [x] **TASK-1.2 [Task decomposition]** — by stage, then by milestone/increment; each handoff
  is a committed file. Deliverable: `§3`.
- [x] **TASK-1.3 [Communication protocol]** — artifact-based; stable ID vocabulary; one writer
  per file; provenance rule for QA. Deliverable: `§4`.
- [x] **TASK-1.4 [Memory/state]** — repo as shared memory; living vs append-only; no hidden
  state. Deliverable: `§5`.
- [x] **TASK-1.5 [Failure recovery]** — gate failure, ambiguity, blocked increment, bounded
  waits, autonomy limits. Deliverable: `§6`.
- [x] **TASK-1.6 [Evaluation/observability]** — DoD per increment, exit criteria per
  milestone, git + change log as trace, QA as independent evidence. Deliverable: `§7`.

## Protocols

- [x] Handoff contracts and their artifact paths (`AGENT-TOPOLOGY.md` §3).
- [x] Autonomy boundary: the assistant never pushes, deploys, deletes, or publishes.

## Evaluation

- [x] Per-increment DoD: `WORKING-AGREEMENT.md` §5.
- [x] Per-milestone exit criteria: `ROADMAP.md` §2.
- [x] Independent verification: `05-qa/results/` (immutable to the builder).

## Commands

- N/A (governance artifact). The topology is validated by observing that every handoff in
  `§3` exists as a committed file.

## Quality checklist

- [x] Topology, roles, and prohibitions defined.
- [x] Handoff contracts named.
- [x] Communication and ID scheme defined.
- [x] Memory locations + mutability defined.
- [x] Recovery/escalation defined.
- [x] Evaluation signals defined.
- [x] Human gate for irreversible actions.
