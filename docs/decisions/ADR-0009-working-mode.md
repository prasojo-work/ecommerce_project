# ADR-0009: Delivery working mode — assistant authors, founder reviews

- **Status:** Accepted
- **Date:** 2026-10-07
- **Deciders:** Founder

## Context

The baseline delivery approach (`PLAN.md` §7, "teaching mode") had the founder personally type every file the assistant proposed, for learning by transcription.

In practice this produced a recurring failure mode: the assistant's chat output is rendered as Markdown, and sequences containing `${...}` (JavaScript template literals) were interpreted as math and replaced with placeholders such as `MATH1`, while literal angle-bracket markup surfaced as `HTML11`. The pasted files were silently corrupted, and the resulting build/type-check failures were traced back to the paste, not the code.

The founder reviewed this and chose to change how work is produced.

## Options considered

1. **Keep teaching mode (founder transcribes).** Pros: the founder types every line; strong for learning. Cons: chat rendering mangles `${...}` and angle brackets; slow; error-prone; wasted cycles debugging corrupted pastes.
2. **Assistant writes, with no gates or tests.** Pros: fastest. Cons: no verification; quality and regressions unmanaged; poor fit for a portfolio that must demonstrate engineering discipline.
3. **Assistant authors, gate-enforced, committed per increment; founder reviews.** Pros: removes the paste-mangling failure mode; every increment is verified (lint, types, tests, build) and committed with a clear message; the founder reviews a *working* increment. Cons: the founder types less; review shifts to reading diffs and running the app.

## Decision

Adopt **Option 3**. For each increment the assistant:

1. writes the code directly to the repository;
2. keeps it passing all quality gates — `ruff`, `basedpyright`, ESLint, `tsc`, the unit tests, and the production build;
3. adds unit tests (backend and frontend);
4. commits the increment (`git add` + `git commit`).

The founder reviews the increment and decides whether to continue or to request changes or clarification.

## Consequences

- **Positive:** the mangled-paste class of bug disappears; each increment is green and individually reviewable in git history; testing discipline is enforced.
- **Negative / costs:** the founder no longer builds keyboard-level familiarity by typing; the review step becomes essential to catch what the gates cannot (UX, intent).
- **Follow-ups:** `PLAN.md` §7 updated; change recorded in `CHANGE-LOG.md` v0.1.2.

## Reversibility

**High.** This is a process choice, not an architectural one; reverting to teaching mode is a documentation change with no code impact.
