# UX & Design Direction — NORDVIK

> Consulted hat: **Senior UI/UX**. Owner: Founder.
> A portfolio store must *look* trustworthy in the first three seconds — especially in a category with ~92% cart abandonment, where trust is the product.

---

## Design principles

1. **Affordable-by-design, not cheap.** Clean, calm, Scandinavian-minimal. Whitespace and hierarchy, not decoration.
2. **Clarity over cleverness.** Price, availability, and shipping cost are always visible and unambiguous.
3. **Mobile-first.** The primary Indonesian shopper is on a phone. Design for the smallest screen, enhance upward.
4. **Trust at every step.** Delivery expectations, return policy, and payment status are surfaced, never hidden.
5. **Accessible by default.** Accessibility is a requirement (`NFR-2`), not a later polish pass.

## Information architecture

```
Home
├── Shop (all products)
│   ├── Category: Living room
│   ├── Category: Bedroom
│   ├── Category: Dining & kitchen
│   ├── Category: Storage & small-space
│   └── Category: Home accessories
├── Search results (query + filters)
├── Product detail ( /product/:slug )
├── Cart
├── Checkout (address → shipping → payment → confirmation)
├── Account
│   ├── Profile
│   ├── Addresses
│   └── Orders (list → detail)
└── Admin (separate area)
    ├── Products / Variants / Inventory
    └── Orders
```

## Key flows

**Browse → buy (the money flow):**
`Home/Shop → Category or Search → Product detail → Add to cart → Cart → Checkout → Mock payment → Order confirmation`

**Return visit:** `Login → Account → Orders → Order detail`

### Checkout flow — designed against abandonment

Four short steps, each showing a persistent order summary and the running total:
1. **Address** — select saved or add new.
2. **Shipping** — options with cost and ETA shown *before* payment (kills the "surprise cost" abandonment driver).
3. **Payment** — mock/sandbox method; clearly labelled "demo — no real charge".
4. **Confirmation** — order number, summary, and what happens next.

Guardrails: validate inline, never lose entered data on error, never block the back button.

## Visual language (design tokens)

| Token | Value | Use |
|---|---|---|
| `--color-bg` | `#FAFAF8` (warm off-white) | Page background |
| `--color-surface` | `#FFFFFF` | Cards, panels |
| `--color-ink` | `#1A1A1A` | Primary text |
| `--color-muted` | `#6B6B6B` | Secondary text |
| `--color-accent` | `#1F5E4B` (deep green) | Primary actions, brand |
| `--color-danger` | `#B3261E` | Errors, destructive |
| `--radius` | `4px` | Cards, buttons (restrained) |
| `--space-unit` | `4px` scale (4/8/12/16/24/32/48) | Spacing |
| Display font | geometric sans (e.g. Inter / system stack) | Headings |
| Body font | same family, different weights | Body |

Palette is intentionally narrow: neutrals + one accent. This reads as "considered brand" rather than "template".

## Responsive breakpoints

- **Base (mobile):** single column; sticky "Add to cart" on product detail.
- **≥ 640 px (sm):** two-column product grids.
- **≥ 1024 px (lg):** three-/four-column grids, persistent filter sidebar.
- **≥ 1280 px (xl):** max content width capped (~1280 px), generous margins.

## Component inventory (initial)

`Button` · `Input` · `Select` · `ProductCard` · `ProductGallery` · `PriceTag` · `StockBadge` · `QuantityStepper` · `CartLineItem` · `OrderSummary` · `Breadcrumbs` · `Pagination` · `FilterPanel` · `Toast` · `EmptyState` · `SkeletonLoader` · `Header` · `Footer`.

## Accessibility commitments (NFR-2)

- Full keyboard operability; visible focus rings; logical tab order.
- Semantic landmarks (`header`/`nav`/`main`/`footer`), one `h1` per page, correct heading levels.
- Alt text for product imagery; `aria-label` for icon-only controls.
- Contrast ≥ 4.5:1 for text, ≥ 3:1 for large text and UI boundaries.
- Respect `prefers-reduced-motion`.
- Forms: labels always visible, errors announced to assistive tech.

## Content & tone

Plain, warm, confident. Prices in IDR with clear formatting (e.g. `Rp 1.299.000`). Microcopy that answers the shopper's next question ("Free delivery over Rp 500.000", "Ships in 3–5 days", "Demo store — payments are simulated").
