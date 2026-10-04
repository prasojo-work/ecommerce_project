# ADR-0007: Brand name — NORDVIK

- **Status:** Accepted
- **Date:** 2026-10-04
- **Deciders:** Founder
- **Related:** `01-business/STRATEGY.md` (brand proposal)

## Context

The store needs a brand name that reads as a design-led home-goods brand, evokes the IKEA reference without copying it, and is pronounceable in both English and Indonesian. The name appears throughout the documentation, will appear in the UI, and will be the public name of the portfolio artifact.

## Options considered

1. **NORDVIK** — Nordic feel, memorable, clearly a "home" brand, easy to pronounce in both languages.
2. **Nestora** — warm, "nest" connotation; softer, less differentiated.
3. **Hemora** — "hem" (home, Swedish); pleasant but ambiguous to non-Scandinavians.
4. **Kasa Living** — "kasa" (house, Indonesian/Spanish overlap); good local resonance, weaker internationally.

## Decision

Use **NORDVIK** as the brand name. Approved by the founder on 2026-10-04.

## Consequences

- **Positive:** one clear name across docs, repo, and UI; strong fit with the Scandinavian design direction.
- **Negative / costs:** the name must be checked against trademarks/domains before any real-world use (not a concern for a portfolio); renaming later would touch many surfaces.
- **Follow-ups:** use `NORDVIK` in the storefront header, page titles, and `README`; keep the name configurable in one place in code (a single brand constant) to keep a future rename cheap.

## Reversibility

**High in principle, medium in practice.** A rename is conceptually simple but touches documentation, UI strings, and any seeded data — so it is best to settle now.
