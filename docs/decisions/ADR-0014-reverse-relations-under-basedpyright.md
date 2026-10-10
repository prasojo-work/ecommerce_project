# ADR-0014 — Reverse foreign-key access under basedpyright

- **Status:** Accepted
- **Date:** 2026-10-10
- **Deciders:** Founder
- **Consulted hats:** senior_backend

## Context

The backend type-checks with `basedpyright` in `standard` mode against `django-stubs`. That
combination understands fields, forward foreign keys, managers, querysets, and model methods.

It does not understand **reverse** foreign-key accessors. During `M1.2` the catalogue models gained
`related_name="children"` on `Category.parent` and `related_name="images"` on `ProductImage.product`.
`basedpyright` reported `reportAttributeAccessIssue` for `category.children` and `product.images`:
both are real at runtime, and neither exists as far as the checker is concerned.

The cause is structural rather than a version lag. django-stubs implements reverse-relation
inference as a **mypy plugin**. pyright has no equivalent plugin mechanism, so no configuration
makes `product.images` visible to it.

This is not academic. `M1.3` writes the first serialiser that traverses a relation, and every
surface after it does the same, so the convention has to be chosen before that code exists rather
than retrofitted across it.

## Options considered

1. **Query explicitly.** `ProductImage.objects.filter(product=product)` instead of
   `product.images.all()`. Pros: fully typed, nothing suppressed, and `Meta.ordering` still
   applies, so behaviour and ordering are identical. Cons: marginally more verbose, and the
   reverse accessor becomes something the codebase avoids by convention rather than by compilation.
2. **Pass relation names as strings.** `prefetch_related("images")`,
   `filter(images__isnull=False)`. Pros: typed at the call site and idiomatic for avoiding N+1
   regardless of this decision. Cons: the string itself is unchecked, so a typo fails at runtime.
3. **Declare the accessors on the models**, e.g. `images: RelatedManager[ProductImage]`. Pros:
   `product.images` becomes readable and typed. Cons: a hand-written annotation per reverse
   relation, which must be kept in step with `related_name` and can silently drift from it.
4. **`cast` at the call site.** Pros: keeps the natural accessor. Cons: scatters type assertions
   through application code and suppresses real errors — the failure mode casts are worst at.
5. **Move type checking to mypy**, which has the plugin. Pros: reverse relations work. Cons:
   reverses a settled toolchain decision, and either adds a second checker or replaces one that is
   otherwise green.

## Decision

Adopt **option 1: query explicitly**, with option 2 allowed where the query needs it anyway.

- Application and model code reach relations through the manager —
  `ProductImage.objects.filter(product=product)` — not through the reverse accessor.
- `prefetch_related("images")` and `__`-lookups in `filter()` / `order_by()` are preferred for
  reads that need them. They are strings either way, and they avoid N+1.
- Never `cast` a reverse accessor.
- The convention is recorded here and carried in `RUNBOOK.md` §8 as a gotcha, so the next person
  meets it before writing the code rather than during review.

## Consequences

- Every relation traversal is checked by the type tool, with no suppressions anywhere.
- `Meta.ordering` still applies to explicit queries, so a manager query and a reverse accessor
  return rows in the same order. The `M1.1` tests already assert this for `ProductImage`.
- A relation name inside a string (option 2) is the one remaining place a typo escapes the checker;
  tests that exercise the query are the guard.
- Parts of the codebase read less like textbook Django. That is worth knowing before someone
  "corrects" it back, which is why this record exists.
- `basedpyright` stays the single type checker and no dependency changes.

## Reversibility

**Cheap.** This is a convention, not a dependency or a schema decision. Reversing it means
replacing manager queries with accessors where they appear, and revisiting this record. Nothing
about the models, the API contract, or the toolchain is entailed either way.

## References

- `docs/04-delivery/RUNBOOK.md` §8 — the gotcha entry this decision is summarised in
- `docs/03-architecture/DATA-MODEL.md` §2 — the relations in question
- `docs/04-delivery/ROADMAP.md` — `M1.1` (where the relations were added), `M1.3` (the first consumer)
- django-stubs README — reverse relations are provided by the mypy plugin
