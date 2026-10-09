# TODO — Code Reviewer (raw working file)

> Raw output of the `senior_code_reviewer` hat for LYSHEIM, committed for transparency. At
> Stage 5 there is **no application code to review yet**, so this file reviews the *planning
> artifacts* and records the review standard. The standard itself is
> [`../06-quality/CODE-REVIEW-STANDARD.md`](../06-quality/CODE-REVIEW-STANDARD.md).

## Context

- Change under review: the Stage 0–4 planning set (docs only).
- Scope: correctness, security, maintainability, testing, and performance of the *plan*.
- CI status: not applicable (no code); gates defined for M0.

## Review Findings

- [ ] **REVIEW-1.1 [Testing]** — Location: `SCOPE.md`, `ROADMAP.md`. Issue: the frontend
  end-to-end strategy is only "optional Playwright"; the checkout happy path is the one flow
  a reviewer will actually exercise. Severity: **Suggestion**. Recommendation: make one E2E
  happy-path journey **required** by M4/M7.
- [ ] **REVIEW-1.2 [Testing]** — Location: `SCOPE.md` NFR-7. Issue: a coverage target is set
  for the backend domain/services but none for the frontend. Severity: **Suggestion**.
  Recommendation: set a modest frontend target (e.g. key components/pages) so "tested" is
  measurable on both sides.
- [ ] **REVIEW-1.3 [Correctness]** — Location: `DATA-MODEL.md` §3, `SCOPE.md` `US-5.5`. Issue:
  the order-status transition matrix is described but not fully enumerated (e.g. can
  `cancelled` be reached from `paid`? from `delivered`?). Severity: **Suggestion**.
  Recommendation: enumerate the legal transitions explicitly before M4.
- [ ] **REVIEW-1.4 [Performance]** — Location: `API.md` §4. Issue: catalog/PDP reads with
  variants and images are an N+1 risk; no `select_related`/`prefetch_related` guidance is
  stated. Severity: **Suggestion**. Recommendation: state the eager-loading requirement for
  list/detail queries and assert query counts in tests.
- [ ] **REVIEW-1.5 [Security]** — Location: `API.md` §6. Issue: `POST /orders` requires an
  `Idempotency-Key`; behaviour when it is missing is unspecified. Severity: **Suggestion**.
  Recommendation: define a `400` (missing key) vs the duplicate-suppression behaviour.
- [ ] **REVIEW-1.6 [Maintainability]** — Location: `_working/TODO_*.md`. Issue: file names use
  hyphens where the persona prompts specify underscores; this is intentional for readability.
  Severity: **Nitpick**. Recommendation: keep as-is (consistency within the repo) — noted only
  for traceability.

## Proposed Code Changes

- None at this stage; the recommendations above become acceptance criteria in the relevant
  increments (M2/M4/M7) rather than edits to planning docs.

## Commands

- Defined for M0 in [`../04-delivery/RUNBOOK.md`](../04-delivery/RUNBOOK.md) §3–§4.

## Quality checklist

- [x] Each finding has a location, explanation, and recommendation.
- [x] Security-relevant findings prioritised.
- [x] Feedback is specific and constructive.
- [x] Overall recommendation: **approve with suggestions** for the planning set.
