# ADR-0012 — Image licensing and attribution

- **Status:** Accepted
- **Date:** 2026-10-09
- **Deciders:** Founder
- **Consulted hats:** senior_business_strategist, senior_cybersecurity

## Context

Product imagery comes from the reference set in `some_source/` (100 Openverse images with a
`manifest.csv` of creator, licence, and source). The licences are mostly **CC BY** and
**CC BY-SA**, with a few **CC BY-ND** and public-domain (**PDM**) items. Shipping these in a
public portfolio without attribution would breach the licences, and ND items restrict
derivative works (e.g. heavy editing).

## Options considered

1. **Ignore licences.** Pros: none. Cons: licence breach on a public, indexed portfolio.
2. **Buy/licence bespoke imagery.** Pros: cleanest. Cons: cost and time, out of scope for a
   simulated business.
3. **Use the CC set with a complete attribution page and a curation rule.** Pros: free,
   legal, and it demonstrates licence awareness. Cons: a required credits page and a
   curation step that excludes unsuitable or ND-restricted images.

## Decision

Use **option 3**:

- Every shipped image gets an **`image_credit`** record (title, creator, licence, source,
  source page) populated from `manifest.csv`, rendered on `/pages/credits` (`US-6.1`).
- **Prefer** `BY`, `BY-SA`, and `PDM` images. **Exclude** `BY-ND` images from any cropping or
  alteration; if an ND image is unsuitable for the layout, it is dropped rather than edited.
- Keep `manifest.csv` in the repository as the provenance record.
- Curate during **M1**: the images are keyword-matched and some are semantically wrong (e.g.
  a press photo for "cabinet"), so only fitting images ship.

## Consequences

- The portfolio is licence-compliant and shows the founder respects third-party rights — a
  signal clients notice.
- `EPIC-6` `US-6.1` becomes a **Must**, and M1 gains a curation task.
- The credits page doubles as an honest statement of how the demo was assembled.

## Reversibility

**Cheap.** Swapping to purchased/licensed imagery later just replaces the files and their
credit rows.

## References

- `docs/02-product/SCOPE.md` §4 (`US-6.1`)
- `docs/PLAN.md` §9 (`RISK-5`)
