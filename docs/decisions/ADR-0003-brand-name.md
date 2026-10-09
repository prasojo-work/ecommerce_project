# ADR-0003 — Brand name: LYSHEIM

- **Status:** Accepted
- **Date:** 2026-10-09
- **Deciders:** Founder
- **Consulted hat:** senior_business_strategist

## Context

The store needs a brand name that (a) signals the IKEA-adjacent home-goods category, (b)
reads and pronounces cleanly for an **international, English-first** audience billed in
**USD**, (c) is not an existing trademark we are aware of in this space, and (d) works as a
wordmark. This is a *simulated* business used for portfolio purposes, but the name must look
like a real, considered brand.

## Options considered

| Name | Rationale | Concern |
|---|---|---|
| **LYSHEIM** | Old Norse *lys* (light) + *heim* (home) → "light home"; warm, evocative, two clean syllables | Slightly Nordic-specific for a global audience |
| NORDHAVEN | "northern haven"; very clear home-goods signal | "Nord"-prefixed names are crowded |
| VIDDE | Swedish for "heath / open country"; short and distinctive | Meaning is opaque to a general audience |
| HAVLY | short, modern, tech-forward | Reads more like a SaaS brand than a home-goods brand |

## Decision

**LYSHEIM** — tagline *"Well-made home goods for everyday living."*

## Consequences

- Brand language and design tokens can lean into *light, warmth, and home*.
- Domain and social handles are assumed available for the simulation; a real launch would
  require trademark and domain clearance (explicitly out of scope).
- All documentation, seed data, and UI use `LYSHEIM` consistently.

## Reversibility

**Moderate.** Renaming later touches copy, seeds, and docs. The name lives in seed data and
configuration, not in business logic, so the code cost is low.

## References

- `docs/01-business/STRATEGY.md` (positioning)
