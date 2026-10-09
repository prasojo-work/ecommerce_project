# Code Review Standard — LYSHEIM

> Consulted hat: **Senior Code Reviewer**. Owner: Founder.
> Because the author is also the reviewer, review is a **ritual performed at commit time**,
> not an afterthought. This standard defines what "reviewed" means here and what blocks a
> commit.

---

## 1. Context

- Solo developer + an AI assistant. There is no second human reviewer, so the assistant
  performs a self-review against this standard before every commit, and the founder reviews
  the stage gates and the running demo.
- The standard is deliberately prioritised: **correctness and security block a commit**;
  style never does (formatting is automated).

## 2. Review workflow

1. **Intent first.** Read the increment's goal (the story/AC in `SCOPE.md` or the roadmap
   increment) before reading the diff.
2. **Diff scope.** Separate core logic from generated, config, and migration files.
3. **Gates.** Confirm `ruff`/`basedpyright`/ESLint/`tsc`/tests pass *before* manual reading.
4. **Read for correctness, then security, then maintainability, then performance.**
5. **Tests.** Verify the tests assert behaviour, not merely that code runs.
6. **Decision.** Approve, approve-with-comments, or request changes. Summarise blockers.

## 3. Severity levels

- **Blocking** — a bug, a security gap, a broken contract, or a missing test for new
  behaviour. The commit does not happen until fixed.
- **Suggestion** — an improvement worth doing; record it (a `RISK-*`, a roadmap increment, or
  a `TODO` comment explaining the *why*), but it does not block.
- **Nitpick** — taste; usually not worth mentioning because formatting is automated.

## 4. Review checklist

**Correctness**
- [ ] The change matches the stated intent, not merely "looks plausible".
- [ ] Edge cases handled: empty, zero/negative, not-found, concurrent action.
- [ ] Error paths are explicit and surfaced to the user, never silently swallowed.
- [ ] Money is integer cents; no float arithmetic on prices.
- [ ] State transitions are guarded (e.g. order status).

**Security** (see `SECURITY-BASELINE.md`)
- [ ] All inputs validated server-side at the boundary.
- [ ] Authorization enforced server-side on every endpoint; no IDOR.
- [ ] No secrets, tokens, or PII in code, config, or logs.
- [ ] No raw SQL; ORM/parameterised queries only.
- [ ] New endpoints are throttled where abuse is plausible.

**Maintainability**
- [ ] Names explain intent; functions have a single responsibility.
- [ ] No duplicated logic that should reuse an existing utility.
- [ ] No magic numbers/strings where a named constant belongs.
- [ ] Comments explain *why*, never restate *what*.
- [ ] Fits existing architecture boundaries; no new coupling without an ADR.

**Testing & performance**
- [ ] New behaviour has tests covering the happy path and at least one edge case.
- [ ] Tests assert real behaviour (not just "no exception raised").
- [ ] No N+1 queries on list endpoints; pagination is bounded.
- [ ] No unbounded loops over external calls.

## 5. Language-specific guidance

**Python / Django**
- Type hints on the service/domain layer (ruff `ANN`); no mutable default arguments.
- Context managers for resources; no bare `except:`.
- Migrations reviewed by hand; destructive changes staged (backfill → switch → drop).

**TypeScript / Next.js**
- No unchecked `any` in public interfaces; strict mode stays clean.
- No unhandled promise rejections; event listeners/timers cleaned up.
- User-generated content is escaped; no `dangerouslySetInnerHTML`.

## 6. Definition of "ready to commit"

An increment is ready when every **Blocking**-level box in §4 is satisfied, all gates pass,
and the commit message states the increment and how to run it. This mirrors
[`../WORKING-AGREEMENT.md`](../WORKING-AGREEMENT.md) §5.

## 7. Feedback etiquette (self-review)

- Be specific: cite the file and line, and explain the *why*.
- Distinguish blockers from suggestions explicitly.
- Note good decisions too — the change log records what worked, not only problems.

## 8. Quality checklist

- [x] All logic branches traced against requirements and edge cases.
- [x] Security implications assessed on every new boundary.
- [x] Maintainability evaluated (naming, duplication, complexity).
- [x] Test coverage judged for new and changed behaviour.
- [x] Performance considered for hot paths and data-heavy operations.
- [x] Feedback prioritised (blocking vs. suggestion) and specific.
- [x] A clear overall recommendation is stated for each increment.
