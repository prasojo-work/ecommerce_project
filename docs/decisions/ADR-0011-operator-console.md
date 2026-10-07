# ADR-0011: Operator console — a hardened Django admin with guarded order transitions

- **Status:** Accepted
- **Date:** 2026-10-07
- **Deciders:** Founder
- **Related:** `ADR-0004`, `EPIC-7`, `US-1.3`, `US-7.1`, `US-7.2`

## Context

M5 must deliver `EPIC-7`: persona `P3`, the store operator (the founder), needs to manage the
catalog, stock and orders **without touching the database**. `UX.md` places "Admin (separate area)"
outside the storefront, listing Products / Variants / Inventory and Orders.

Three facts shaped the decision:

1. `django.contrib.admin` is already installed, mounted at `/admin/`, and registered for every
   model. M2 went further and built bespoke `UserAdmin` forms (`accounts/forms.py`), so the project
   has already invested in Django admin as its administration surface.
2. Orders are **immutable snapshots** (an M4 exit criterion) and their status is driven by a
   fulfilment state machine. A generic CRUD screen that lets an operator hand-edit `status`,
   `total` or line-item snapshots would let them silently corrupt purchase history — the exact
   thing the data model forbids.
3. Payments are owned by the `payments` context, and the architecture forbids reaching across
   context boundaries. So an operator must not be able to mark an order `paid` by hand — that
   would create a paid order with no payment record.

## Options considered

1. **Bespoke Next.js admin frontend** — most control and the most impressive screenshot. Cost: a
   second full CRUD surface, its own auth/RBAC, its own tests, and it duplicates work Django gives
   away. It also needs an admin API that the architecture does not define.
2. **Django admin as-is** — zero work, but it exposes `status`, `total`, snapshots and item rows as
   editable fields, which is directly at odds with the immutability requirement, and it has no
   notion of "which orders can legally move to shipped".
3. **Django admin, hardened, with the rules in the domain layer** — keep the generated UI, but put
   the business rules behind service functions and make the console respect them.

## Decision

Take **option 3**.

- The operator console **is** Django admin at `/admin/`, hardened rather than replaced.
- The order state machine lives in `orders/services.py` as framework-free functions
  (`can_transition`, `transition_order`, `cancel_order`) with an explicit `ALLOWED_TRANSITIONS`
  map. It is deliberately **not** written against the admin, so a future UI could reuse it.
- In the console, `status` and every monetary/snapshot field are **read-only**; the only way to
  move an order is the guarded bulk actions (processing → shipped → completed, or cancel), which
  report per-order success and refusal instead of failing silently. Orders cannot be added or
  deleted, and line items are read-only.
- There is deliberately **no "mark as paid" action** — payment is `payments`' job (`ADR-0004`).
- **Cancelling an order returns its reserved stock to the catalog**, in a transaction under row
  lock, and `cancelled` is terminal so the same units cannot be restocked twice.
- Inventory (`US-7.2`) is served by a variant changelist with inline stock editing and a
  stock-level filter (out / low / in stock), which answers the operator's real question:
  *what do I need to reorder?*

## Consequences

- **Positive:** no hand-rolled CRUD; Django's permission model, audit-friendly actions, search,
  filters and date drill-down come free; the fulfilment rules cannot be bypassed by hand; the
  domain layer stays UI-agnostic and testable without HTTP.
- **Negative / costs:** the console looks like Django admin, not like NORDVIK, so it is not a
  showcase surface; the operator needs a staff account; the low-stock threshold (5) and the
  transition map are code, so changing them needs a deploy.
- **Follow-ups:** a bespoke UI later should call the same `orders/services.py` functions. The E2E
  plan's open question about how to test admin journeys (its §13) now resolves to Django admin.

## Reversibility

**High for the UI, high for the rules.** Swapping the console for a custom frontend would not
require touching the state machine. The rules themselves are a handful of functions in one module.
