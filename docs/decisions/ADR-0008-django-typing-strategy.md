# ADR-0008: Type-checking strategy for Django under basedpyright

- **Status:** Accepted
- **Date:** 2026-10-04
- **Deciders:** Founder
- **Related:** `ADR-0002` (Ninja), `NFR-6` (typed code)

## Context

The stack mandates static type checking (backed by `basedpyright`). Django ships **no `py.typed` marker** — it is effectively untyped — so a Pyright-based checker mis-infers Django objects (e.g. a test client response inferred as `WSGIRequest`, which has no `status_code`/`json()`). The two community stub packages both have problems in our context:

- **`django-stubs`** derives most of its value from a **mypy plugin**, which Pyright/basedpyright cannot run; it is documented to produce false positives under Pyright, and it lags new Django releases (we are on Django 6.1).
- **`django-types`** is friendlier to Pyright but less actively maintained and also lags Django releases.

## Options considered

1. **Adopt `django-stubs`** — mypy-oriented; false positives under basedpyright; version lag.
2. **Adopt `django-types`** — more Pyright-friendly; less maintained; version lag.
3. **Minimal third-party typing: use framework-provided typed surfaces; keep Django-specific code thin** — chosen.

## Decision

Do **not** add a Django stub package for now. Instead:

- Prefer **framework surfaces that ship `py.typed`** — notably **Django Ninja**, which provides fully typed schemas and a typed test client (`ninja.testing.TestClient` / `TestResponse`) — for tests and API code.
- Keep Django-specific code (settings, URLs, management wiring) thin and simple, and accept that some Django internals remain effectively `Any`.
- Revisit this decision if/when a stub package maturely supports Django 6 **and** Pyright without the mypy plugin.

## Consequences

- **Positive:** zero extra dependencies; no false-positive noise; tests exercise the real API through a typed client; type checking stays useful where it matters (our own code and the Ninja boundary).
- **Negative / costs:** Django internals aren't type-checked; we may occasionally lose type safety at the ORM/model boundary and lean on runtime tests there.
- **Follow-ups:** document the pattern in code review; reassess at each major Django bump.

## Reversibility

**High.** Adding a stub package later is a dependency + config change, not a rewrite.

## Update — 2026-10-05: concrete configuration

Implementing this decision surfaced that basedpyright, with `useLibraryCodeForTypes` at its default (`true`), reads Django's *untyped source* and infers nonsense — e.g. `models.BooleanField(default=True)` flagged as not assignable to `type[NOT_PROVIDED]`, and `__str__` returning a `CharField`. The configuration that realizes "untyped libraries become `Any`, `py.typed` libraries stay typed":

- `[tool.basedpyright] useLibraryCodeForTypes = false` — Django and django-environ are treated as `Any`; Django Ninja (which ships `py.typed`) stays fully typed.
- `exclude = ["**/migrations"]` (basedpyright) and `[tool.ruff] extend-exclude = ["**/migrations"]` — generated migrations are excluded from both tools.
