# UX & Design — LYSHEIM

> Consulted hat: **Senior UI/UX**. Owner: Founder.
> Inputs: [`SCOPE.md`](SCOPE.md), [`../01-business/STRATEGY.md`](../01-business/STRATEGY.md).
> This document is the developer-ready design spec; it is validated by the QA scenarios in
> `docs/05-qa/`.

---

## 1. Context & design goals

- **Product:** LYSHEIM storefront + operator console. **Platform:** responsive web,
  mobile-first.
- **Segments / jobs:** the Renter (primary) and the Young Family (`SCOPE.md` §2). Both are
  making a **considered, big-ticket** purchase in a category where **~8 in 10 carts are
  abandoned**. The experience must therefore reduce doubt at every step.
- **Constraints:** WCAG 2.1 AA; a coherent LYSHEIM visual language; everything achievable by
  a solo builder.

**Design goals (measurable).**

- [ ] `UX-GOAL-1` Reduce doubt: surface price, dimensions, stock, and shipping cost *before*
  the cart, targeting abandonment below the ~79% category norm.
- [ ] `UX-GOAL-2` Keep the core task (find → add → check out) to a minimal number of steps.
- [ ] `UX-GOAL-3` Pass WCAG 2.1 AA on key routes (axe-clean + keyboard-only review).

## 2. Visual language

LYSHEIM's brand is **light, warm, and homely** (see `ADR-0003`). The interface should feel
calm and editorial, not discount-retail. Generous whitespace, a warm neutral canvas, one
confident accent, and large product imagery.

### Design tokens

```css
:root {
  /* Palette — warm neutrals + a calm brand green */
  --lys-canvas:   #FAF7F2;  /* page background */
  --lys-surface:  #FFFFFF;  /* cards, panels */
  --lys-ink:      #1C1917;  /* primary text */
  --lys-muted:    #57534E;  /* secondary text */
  --lys-border:   #E7E1D8;  /* hairlines, dividers */
  --lys-primary:  #2F6B4F;  /* brand green — primary actions */
  --lys-primary-ink: #FFFFFF;
  --lys-accent:   #B4552E;  /* terracotta — sparing emphasis */
  --lys-success:  #2F6B4F;
  --lys-warning:  #8A5A00;
  --lys-danger:   #A5372C;

  /* Type scale (rem) */
  --lys-fs-xs: 0.75rem; --lys-fs-sm: 0.875rem; --lys-fs-base: 1rem;
  --lys-fs-lg: 1.125rem; --lys-fs-xl: 1.25rem; --lys-fs-2xl: 1.5rem;
  --lys-fs-3xl: 1.875rem; --lys-fs-4xl: 2.375rem; --lys-fs-5xl: 3rem;

  /* Spacing (4px base) */
  --lys-space-1: 4px; --lys-space-2: 8px; --lys-space-3: 12px; --lys-space-4: 16px;
  --lys-space-6: 24px; --lys-space-8: 32px; --lys-space-12: 48px; --lys-space-16: 64px;

  --lys-radius: 8px;
  --lys-radius-lg: 16px;
}
```

- **Typography:** `Inter` for UI; an optional display serif (e.g. `Fraunces`) for hero
  headings to add editorial warmth. Body line length capped at ~70 characters.
- **Color rule:** never encode state by color alone (`SCOPE.md` NFR-2); pair with text or an
  icon. All text/background pairs above must be verified at ≥ 4.5:1 before release.
- **Imagery:** product photography leads. Source webp images are keyword-matched and
  sometimes unsuitable, so every shipped image is curated during M1.

## 3. Information architecture

```
/                       Home — hero, featured products, trust/CTA
/products               Catalog — search, filter, sort, pagination
/products/[slug]        Product detail — gallery, price, stock, add-to-cart
/cart                   Cart — line items, subtotal, shipping estimate
/checkout               Checkout — address → shipping → payment (mock) → confirm
/login  /register       Authentication
/account                Profile + addresses
/orders                 Order history
/orders/[number]        Order detail + status
/pages/about            About
/pages/shipping-returns Shipping & returns
/pages/credits          Image attribution (licensing requirement)
/operator/*             Operator console (form fixed in Stage 3 — see SCOPE §8 D1)
```

## 4. Key user flows

**Flow A — Discover → detail.** Home or category → filter/sort → PDP. States: loading
skeletons, empty category, no search results (with recovery suggestion), image load failure.

**Flow B — Add → cart.** PDP add-to-cart → feedback + header count updates → cart → adjust
quantity (stock-capped) → remove → proceed. States: out-of-stock, quantity exceeds stock,
empty cart.

**Flow C — Checkout.** Cart → address (saved or new) → shipping method → mock payment →
review → confirm → order created → confirmation. States: validation errors, payment failure
with retry, session timeout, duplicate submit protection.

**Flow D — Account.** Register → verify field errors → login → silent refresh → logout.
States: bad credentials, already-registered email, rate-limited (429) message.

**Flow E — Order follow-up.** Order history → order detail → status badge.

**Flow F — Operate.** Operator signs in → manage products/stock → view orders → advance
status. States: validation errors, valid-transition enforcement, low-stock warning.

## 5. States matrix

| Screen | Empty | Loading | Error | Success |
|---|---|---|---|---|
| Catalog | "No products yet" | card skeletons | retry panel | grid + result count |
| PDP | n/a (404 page) | skeleton | retry / 404 | gallery + add-to-cart |
| Cart | "Your cart is empty" + CTA | inline | item error | line items + totals |
| Checkout | n/a | step skeleton | field + payment errors | confirmation |
| Orders | "No orders yet" | skeleton | retry | list of orders |
| Operator | "Nothing here yet" | table skeleton | error toast | table + toasts |

## 6. Component inventory

`HeaderNav`, `Footer`, `Button`, `Input`, `Select`, `Badge`, `Breadcrumbs`, `EmptyState`,
`Skeleton`, `Toast`, `ProductCard`, `ProductGrid`, `ProductGallery`, `CatalogFilters`,
`SortSelect`, `Pagination`, `AddToCartButton`, `QuantityStepper`, `CartLineItem`,
`CartSummary`, `CheckoutSteps`, `AddressForm`, `AddressList`, `ShippingMethodSelect`,
`PaymentMockForm`, `OrderSummary`, `OrderStatusBadge`, `OrderDetailView`, `AuthForm`.

Components are built from tokens above; a new pattern requires a stated gap justification.

## 7. Accessibility requirements

- WCAG 2.1 AA. One `<h1>` per page; logical heading order; landmark regions
  (`header`/`nav`/`main`/`footer`); a "skip to content" link.
- Full keyboard operability with a visible focus ring; logical tab order; no focus traps
  except in modals, which return focus on close.
- Form fields have associated labels; validation errors are announced via `aria-live` and
  linked with `aria-describedby`.
- Meaningful `alt` text for product images; decorative images have empty `alt`.
- Touch targets ≥ 44×44 px; no color-only signalling.
- Automated check: `axe` on key routes in CI (M6), plus a keyboard-only manual pass.

## 8. Responsive

Mobile-first. Breakpoints: `sm 640`, `md 768`, `lg 1024`, `xl 1280`. Layouts adapt
intentionally (e.g. filters collapse into a drawer on mobile; PDP gallery becomes a swipeable
carousel rather than a shrunk grid).

## 9. Content & microcopy

Plain, warm, jargon-free, honest. Shipping cost and return policy are stated up front. Error
messages name the problem and the fix ("That email is already registered — try signing in.").
Prices are formatted in USD (`$1,240.00`).

## 10. Validation plan

Every UI increment ships a scenario file in `docs/05-qa/scenarios/` (normal + edge cases +
expected result). A separate **tester agent** executes them in another session and records
results in `docs/05-qa/results/` (immutable to the builder, per `WORKING-AGREEMENT.md` §3).
Post-launch, UX-GOAL-1 is measured through the funnel events captured in Phase 2.
