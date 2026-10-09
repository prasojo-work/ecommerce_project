# ADR-0008 — Cart model and guest merge (D2)

- **Status:** Accepted
- **Date:** 2026-10-09
- **Deciders:** Founder
- **Consulted hats:** senior_backend, senior_ui_ux, senior_system_architect

## Context

`SCOPE.md` `US-3.5` requires a persistent cart and left **decision D2** open: must a shopper
sign in before adding to cart? In this category ~8 in 10 carts are abandoned and the primary
persona (the Renter) shops on mobile, so demanding an account before the cart would raise
friction exactly where it hurts most.

## Options considered

1. **Sign-in required.** Pros: simplest data model. Cons: highest friction; contradicts the
   strategy's anti-abandonment goal.
2. **Client-only cart (localStorage).** Pros: trivial. Cons: not the source of truth, lost
   across devices, no server-side pricing/stock validation, abandoned-cart data unusable.
3. **Server-side cart keyed by a signed cookie for guests, merged on login.** Pros: low
   friction, single source of truth, validates stock server-side, produces data for Phase 2.
   Cons: merge logic, cookie handling, guest-cart expiry.

## Decision

Use **option 3**. A cart is owned by either a `user` (authenticated) or a signed `cart`
cookie (guest). On login, the guest cart is **merged** into the user's cart; conflicting
lines are summed and clamped to available stock. Guest carts expire after a documented
window (default 30 days) and are eligible for the Phase 2 abandoned-cart analysis.

## Consequences

- The cart is always the server's truth, so prices and stock are validated centrally.
- Extra work: a signed cookie, a merge routine, and expiry — all small and well-tested.
- Enables the Phase 2 funnel/abandonment analysis from real data.

## Reversibility

**Moderate.** Dropping guest carts later is simple (require sign-in); the merge code becomes
dead and can be removed. The data model supports both.

## References

- `docs/02-product/SCOPE.md` §8 (D2)
- `docs/03-architecture/API.md` §5
- `docs/03-architecture/DATA-MODEL.md` §2 (`cart`)
