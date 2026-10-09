# Working Agreement

> How LYSHEIM is built, increment by increment. Recorded as a decision in
> [`decisions/ADR-0004-working-agreement.md`](decisions/ADR-0004-working-agreement.md).
> This file is binding for the assistant/builder; amend it only via a new ADR.

## 1. The rules

1. **Small increments.** Every commit is one small, demoable step. No "big bang" changes.
2. **Gates pass before commit.** Each increment must pass formatting and type checking. If a
   gate breaks, fix it *before* committing. The exact tooling is in §2.
3. **Tests ship with the code.** Every increment gets unit tests using mock/fixture data,
   and they must pass.
4. **Commit locally, never push.** After tests pass: `git add` + `git commit`. The assistant
   **does not `git push`**; the founder decides when code reaches GitHub.
5. **Scenario-based QA when UI exists.** For each feature the assistant writes a Markdown
   scenario file with normal and edge cases plus the expected result. A separate **tester
   agent** executes them in another session. See §3 for the provenance rules.
6. **Run instructions after each increment.** The assistant states how to run and verify the
   increment manually; these accumulate in `docs/04-delivery/RUNBOOK.md`.
7. **Seeding.** The database is seeded with dummy data via an idempotent management command
   (`python manage.py seed`, with `--reset`).
8. **Configuration over code.** Every external connection value comes from the environment,
   so deploying means changing configuration only, never code.

## 2. Quality gates and strictness

| Where | Setting | Rationale |
|---|---|---|
| Backend lint/format | `ruff` with `E,F,I,UP,B,C4,SIM,RUF,DJ` | Standard senior baseline. |
| Backend types | `basedpyright` **standard** mode | `strict` mode on Django's dynamic ORM produces mostly noise; `standard` + `django-stubs` is the pragmatic choice. |
| Backend annotations | ruff `ANN` on the **service/domain layer only** | Requires type hints where they add real value; not on migrations, admin, or settings. |
| Frontend types | TypeScript `strict: true` | Non-negotiable and standard. |
| Frontend lint | ESLint + Next `core-web-vitals` + `@typescript-eslint` **recommended** | Type-aware linting is deferred; can be added later if the codebase stays clean. |
| Formatting | `ruff format` (backend), Prettier (frontend) | Deterministic formatting removes style debates. |

A `pre-commit` hook runs the format and type gates automatically so rule (2) is enforced by
tooling, not by discipline alone.

## 3. QA protocol (tester agent)

- **Scenarios** live in `docs/05-qa/scenarios/<feature>.md`. They are written by the
  assistant and are **mutable** — the assistant may refine or remove a scenario.
- **Results** live in `docs/05-qa/results/<feature>.md`. They are written by the **tester
  agent** and are **immutable** to the assistant. The assistant may *delete* a stale result
  file (to invalidate a run), but must **never edit** the tester's result text.
- Each scenario states: the preconditions, the steps, the expected result, and whether it is
  a normal or an edge case.

## 4. Defaults

- **Branch:** commit directly to `main` (solo, clean linear history, never pushed).
- **Commit style:** Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`,
  `test:`).
- **Planning commits:** one `docs:` commit per stage gate.
- **Raw agent TODOs:** committed under `docs/_working/TODO_<role>.md`.

## 5. Definition of "done" per increment

An increment is done when:

- [ ] The change is small and demoable.
- [ ] Formatting and type gates pass.
- [ ] Unit tests pass (and new behaviour is covered).
- [ ] If UI changed, a QA scenario exists.
- [ ] How to run it has been stated.
- [ ] It is committed locally (not pushed).
