# ADR-0010: Checkout pricing, shipping selection and order numbering

- **Status:** Accepted
- **Date:** 2026-10-07
- **Deciders:** Founder
- **Related:** `ADR-0004`, `DATA-4.1`, `US-5.2`

## Context

Building M4 (checkout & orders) forced four questions the existing docs leave open:

1. **Which price does an order charge?** `cart_item` carries a `unit_price_snapshot`, and `DATA-MODEL`'s principle is "orders copy the price … that applied at purchase". It does not say whether checkout re-reads the current catalog price or honours the snapshot taken when the item was added to the cart.
2. **Where does the shipping selection live?** `DATA-MODEL` enumerates `order` with a single `shipping_cost` column and models no shipping entity at all — yet `ARCHITECTURE.md` §4 assigns "shipping" to the `orders` app, and `UX.md` requires shipping *options with cost and ETA shown before payment*.
3. **What shape is `order.number`?** `DATA-MODEL` calls it a "human ref, unique" and specifies no format.
4. **How is the idempotency key transported?** `ARCHITECTURE.md` §7 says "the client sends an idempotency key" but not through which channel.

## Options considered

**1. Price source**

1. **Re-read the catalog at checkout** — always current, and arguably what "applied at purchase" means. Cons: the total can differ from what the cart displayed, which is exactly the "surprise cost" abandonment driver `US-5.2` targets.
2. **Honour the cart's `unit_price_snapshot`** — the shopper is charged what they were shown. Cons: a stale cart locks in an old price indefinitely.

**2. Shipping**

1. **Add a `shipping_method` table** — most normalised, but invents an entity the data model deliberately omits, and needs admin UI (M5) to be useful.
2. **Options in code + two snapshot columns on `order`** — no new table; the chosen option is frozen onto the order like every other purchase-time value.
3. **`shipping_cost` only** — zero drift, but the order loses which option was chosen, so history cannot be displayed faithfully.

**3. Numbering**

1. **`Max(id) + 1`** — simple, racy.
2. **A dedicated Postgres sequence** — robust, but Postgres-specific and adds schema objects.
3. **Derive from the primary key** — unique and monotonic by construction, no extra schema.

## Decision

1. **Price:** checkout charges the cart's `unit_price_snapshot`, not the live catalog price. The anti-surprise promise in `US-5.2` outranks defending against a stale-price edge case, and it gives the `unit_price_snapshot` column a real purpose.
2. **Shipping:** options are defined in code (`backend/orders/shipping.py`) as `standard` and `express`; standard is free at or above **Rp 500.000**, mirroring the customer-facing copy in `UX.md`. Two additive `order` columns record the choice: `shipping_method` (code) and `shipping_method_name` (display snapshot). This is the one deliberate extension to `DATA-4.1` beyond a straight read.
3. **Numbering:** `NDV-<YYYY>-<zero-padded pk>`, e.g. `NDV-2026-000123`. Built in `Order.save()` in two writes inside the caller's transaction: a throwaway unique placeholder first, then the real reference once the primary key exists.
4. **Idempotency:** an optional `idempotency_key` field in the `POST /orders` body. A replay returns the existing order with `200` instead of creating a second one; when the client omits it, the server generates one.

## Consequences

- **Positive:** the charged total can never surprise the shopper; order history is fully self-describing without joining the catalog; no new tables, so no migration risk and no M5 dependency; duplicate submits are provably idempotent.
- **Negative / costs:** shipping options cannot be edited without a deploy (acceptable while the set is fixed, and M5 can revisit it); a cart left open keeps its original price; the two-write `Order.save()` is slightly unusual and is commented as such.
- **Follow-ups:** if shipping options need to be admin-managed, promote them to a table under the `orders` app and supersede this ADR. A price-change notification at checkout would remove the stale-price caveat.

## Reversibility

**Medium.** The pricing rule is a one-line change in `orders/services.py`. The two columns are additive and nullable-free only because every row is created through one code path; dropping them is a routine migration. The number format is cosmetic but already persisted in any existing rows, so changing it later would leave mixed formats in history.
