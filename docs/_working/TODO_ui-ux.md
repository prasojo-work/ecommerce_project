# TODO — UI/UX (raw working file)

> Raw output of the `senior_ui_ux` hat for LYSHEIM, committed for transparency per the
> working agreement. The curated, reviewer-facing version is
> [`../02-product/UX.md`](../02-product/UX.md).

## Context

- Product: **LYSHEIM** — responsive web storefront + operator console.
- Design system: none yet (new brand, 2026-10-09). Tokens proposed in `UX.md` §2.
- Segments / JTBD: the Renter (primary) and the Young Family — a considered, big-ticket
  purchase (`SCOPE.md` §2).
- Constraints: WCAG 2.1 AA; coherent LYSHEIM visual language; solo-buildable.

## Design Plan

- [ ] **UX-PLAN-1.1 [Discover → detail flow]**:
  - Goal: find a suitable product quickly and understand price/stock/dimensions.
  - Research basis: only ~2 in 10 carts convert; surfacing price/shipping early reduces
    abandonment (strategy §3 `STRAT-ANALYSIS-1.3`).
  - States: loading skeleton, empty category, no-results, image failure.
  - Success metric: landing→PDP rate; PDP→add-to-cart rate.
- [ ] **UX-PLAN-1.2 [Add → cart flow]**:
  - Goal: get the right item into the cart with confidence.
  - States: out-of-stock, quantity > stock, empty cart.
  - Success metric: PDP→add-to-cart rate; cart→checkout rate.
- [ ] **UX-PLAN-1.3 [Checkout flow]**:
  - Goal: complete a mock purchase without surprise cost.
  - States: field validation, payment failure + retry, session timeout, double-submit guard.
  - Success metric: checkout completion; abandonment below the ~79% category norm.
- [ ] **UX-PLAN-1.4 [Account flow]**:
  - Goal: register / sign in / stay signed in.
  - States: bad credentials, duplicate email, 429 rate-limit message.
  - Success metric: registration and login completion rates.
- [ ] **UX-PLAN-1.5 [Operate flow]**:
  - Goal: keep catalog, stock, and orders correct.
  - States: validation errors, invalid status transition, low-stock warning.
  - Success metric: operator task completion without support.

## Design Items

- [ ] **UX-ITEM-1.1 [Design tokens]**:
  - Purpose: single source of truth for color, type, spacing.
  - Variants/States: n/a.
  - Accessibility notes: verify text/background pairs ≥ 4.5:1.
  - Handoff spec: CSS variables in `UX.md` §2.
- [ ] **UX-ITEM-1.2 [Component inventory (30 components)]**:
  - Purpose: reusable UI built from tokens.
  - States: each component documents default/hover/focus/disabled/error as applicable.
  - Accessibility notes: focus-visible rings, labels, semantics per component.
  - Handoff spec: `UX.md` §6.
- [ ] **UX-ITEM-1.3 [States matrix]**:
  - Purpose: ensure empty/loading/error/success are designed for every screen.
  - Handoff spec: `UX.md` §5.
- [ ] **UX-ITEM-1.4 [Accessibility checklist]**:
  - Purpose: WCAG 2.1 AA conformance on key routes.
  - Handoff spec: `UX.md` §7; automated via axe in M6.

## Proposed Specs / Code Changes

- Tokens, palette, type scale, and spacing are specified as CSS variables in `UX.md` §2 and
  will become `frontend/src/app/globals.css` at M0/M1.

## Commands

- Automated a11y check (planned, M6): `npm run axe:audit` against key routes.
- Automated performance check (planned, M6): Lighthouse against catalog and PDP.
