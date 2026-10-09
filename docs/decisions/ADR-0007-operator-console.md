# ADR-0007 — Operator console (D1)

- **Status:** Accepted
- **Date:** 2026-10-09
- **Deciders:** Founder
- **Consulted hats:** senior_backend, senior_technical_lead, senior_ui_ux

## Context

`SCOPE.md` `EPIC-5` requires a console to manage categories, products, images, inventory, and
order status. This was left open as **decision D1**. Building a bespoke operator UI in Next
is more visually impressive but doubles the frontend surface for a solo developer with a
fixed v1 finish line (`RISK-1`, `RISK-4`).

## Options considered

1. **Django admin.** Pros: exists on day one, is secure and battle-tested, covers CRUD and
   order edits; near-zero build cost; "boring tech" that a senior would choose. Cons: looks
   like Django admin, not a bespoke product; less frontend showcase.
2. **Custom Next.js console.** Pros: consistent design language, a stronger frontend
   portfolio signal. Cons: substantial extra scope (auth for operators, tables, forms,
   validation, upload) that competes with finishing v1.
3. **Hybrid.** Django admin now, a custom console later for the three highest-value tasks
   (products, stock, order status).

## Decision

Ship **Django admin as the v1 operator console**, customized with list filters, search, and
inline editing so it is genuinely usable. A **custom Next console is deferred to Phase 1.5**
(option 3's hybrid path), to be reconsidered only after v1 is deployed.

## Consequences

- `EPIC-5`'s acceptance criteria are met without spending frontend budget.
- The v1 finish line stays protected; frontend depth is demonstrated through the *storefront*,
  where it matters more.
- Operator access is gated by `is_staff`; a short runbook entry explains how to create an
  operator account.
- The trade-off is an honest, defensible choice rather than a missing feature.

## Reversibility

**Cheap.** The custom console can be added later without touching the domain; Django admin
remains a fallback forever.

## References

- `docs/02-product/SCOPE.md` §8 (D1)
- `docs/03-architecture/API.md` §9
