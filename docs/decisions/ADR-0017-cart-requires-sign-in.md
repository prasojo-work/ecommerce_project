# ADR-0017 — Cart requires sign-in (reverses `D2`)

- **Status:** Accepted
- **Date:** 2026-10-12
- **Deciders:** Founder
- **Consulted hats:** senior_backend, senior_ui-ux, senior_cybersecurity

## Context

`SCOPE.md` `US-3.5` left **decision D2** open — must a shopper sign in before adding to cart? —
and `ADR-0008` answered it with a cookie-keyed guest cart merged on login, on the grounds that
~8 in 10 carts are abandoned and the primary persona shops on mobile, so an account wall would
raise friction exactly where the strategy is weakest.

The Founder reversed that answer on 2026-10-12, while `M3.1` was being built: the catalog stays
public to anonymous visitors, and every cart operation — read, add, update, remove — requires an
access token. The trade-off is taken knowingly rather than overlooked. A first-time visitor who
taps "Add to cart" meets a sign-in screen, and Phase 2's abandonment analysis will only ever see
shoppers who had already signed in. In exchange a cart has exactly one owner, and that owner is an
account rather than a cookie.

## Options considered

1. **Sign-in required** (chosen). Pros: one owner per cart; no cookie to sign, rotate or expire;
   no merge routine; no forged-cart-identifier surface at all (`SECURITY-BASELINE.md`
   `SEC-FIND-1.12`); and the cart's identity is the same token the rest of the API already trusts.
   Cons: friction at the first add for a visitor, and less abandonment data.
2. **Client-only cart (localStorage).** Pros: trivial to build, no server state. Cons: not the
   source of truth, lost across devices, no server-side price or stock validation, and unusable
   for Phase 2 — rejected for the same reasons as in `ADR-0008`.
3. **Signed guest cookie, merged on login** — what `ADR-0008` chose. Pros: the lowest friction,
   and abandonment data for every visitor. Cons: a cookie to sign and expire, a merge routine at
   login, and a cart that exists before its owner does.

## Decision

The cart requires authentication. Every cart endpoint carries the same bearer requirement as the
rest of the account surface, `cart.user` is NOT NULL, there is no `session_key` column, no cart
cookie and no merge step. `M3.2` (guest-cart merge) is removed from the roadmap, and the cart UI
becomes `M3.2`.

## Consequences

- Less code and less to get wrong: no cookie signing, no expiry window, no merge routine, and no
  rows that exist before an account does. A security finding disappears rather than shrinking, and
  the "guest carts expire" retention rule goes with it.
- The friction `ADR-0008` set out to avoid is now accepted deliberately. Anyone can browse; only a
  signed-in shopper can hold a cart. The abandonment rate therefore cannot be measured for
  anonymous visitors — not a defect of the measurement, a property of this decision.
- Reading a cart is side-effect free: an account with no cart gets an empty payload and no row is
  created, so only adding to a cart produces one.
- **Stock.** A cart line is capped by available stock, and a request above it is refused with `409`
  (`US-3.2`) — but that check is an affordance, not a guarantee, because stock moves between the
  cart and checkout. The authoritative, race-safe decrement belongs to order creation in `M4`,
  inside one transaction: either a conditional
  `UPDATE … SET stock_qty = stock_qty - n WHERE id = … AND stock_qty >= n`, treating `rowcount == 0`
  as insufficient, or `SELECT … FOR UPDATE` over the variant rows in a deterministic order so two
  concurrent orders cannot deadlock. `stock_qty` stays `>= 0` by field type and by check
  constraint, and a cart is never allowed to hold a quantity it could not buy.
- `Cart.status` keeps all three values: `converted` at checkout (`M4`), and `abandoned` for a
  signed-in cart that is never converted.

## Reversibility

**Moderate, and asymmetric.** Reversing this later means adding the owner column back, a signed
cookie, and the merge routine — the code `ADR-0008` would have written. That is why the loss is
recorded here rather than treated as an implementation detail. Nothing else in the data model
depends on the choice.

## References

- `docs/02-product/SCOPE.md` §8 (`D2`), `US-3.1`, `US-3.2`, `US-3.5`
- `docs/03-architecture/API.md` §5
- `docs/03-architecture/DATA-MODEL.md` §2 (`cart`), §4
- `docs/04-delivery/ROADMAP.md` — `M3`
- `docs/06-quality/SECURITY-BASELINE.md` — `SEC-FIND-1.12`, retention
- `ADR-0008` — superseded by this decision, for the cart's ownership only
