# Product Scope — NORDVIK MVP

> Consulted hats: **UI/UX**, **Technical Project Manager**. Owner: Founder.
> This document defines **what** we build in Phase 1 and, just as important, **what we refuse to build**.

---

## Personas

- **P1 — Rina, 28, first apartment, South Jakarta.** Rents a 36 m² studio, furnishes it piece by piece on a modest budget. Cares about: small footprint, transparent delivery cost, trust ("will it actually arrive?"). Primary shopper.
- **P2 — Bayu, 36, young family, Tangerang.** Upgrading a living/dining area. Cares about: durability, materials, delivery windows. Higher basket, lower frequency.
- **P3 — Store operator (admin).** The founder. Needs to manage the catalog, stock, and orders efficiently without touching the database.

> **Anti-persona:** the marketplace bargain-hunter looking for the absolute lowest price. We deliberately do not optimize for them (see [`STRATEGY.md`](../01-business/STRATEGY.md)).

---

## Epics

| ID | Epic | Milestone | Priority |
|---|---|---|---|
| `EPIC-1` | Catalog & merchandising | M1 | Must |
| `EPIC-2` | Discovery (search / filter / sort) | M1 | Must |
| `EPIC-3` | Accounts & authentication | M2 | Must |
| `EPIC-4` | Cart | M3 | Must |
| `EPIC-5` | Checkout (address, shipping, mock payment) | M4 | Must |
| `EPIC-6` | Orders (history + detail) | M4 | Must |
| `EPIC-7` | Admin (catalog + orders) | M5 | Must |
| `EPIC-8` | Reviews, wishlist, promos | Phase 2 | Won't (now) |

---

## User stories (with acceptance criteria)

> Format: `As a <persona>, I want <capability>, so that <benefit>.` Acceptance criteria are given as Given/When/Then.

### EPIC-1 · Catalog & merchandising
- [ ] **US-1.1** As a shopper I want to browse products by category so I can find things for a room.
  - *Given* products exist in a category, *when* I open the category page, *then* I see a paginated grid with name, price, and thumbnail.
- [ ] **US-1.2** As a shopper I want a product detail page so I can judge an item before buying.
  - *Given* I open a product, *then* I see gallery images, price, description, variants (size/colour), and stock status.
- [x] **US-1.3** As an admin I want to create/edit/archive products and variants so I can manage the catalog.

### EPIC-2 · Discovery
- [ ] **US-2.1** As a shopper I want to search by keyword so I can find a specific item.
- [ ] **US-2.2** As a shopper I want to filter (category, price range, availability) and sort (price, newest, popularity) so I can narrow results.
  - *Given* filters are applied, *then* URL reflects them (shareable, back-button-safe).

### EPIC-3 · Accounts & authentication
- [ ] **US-3.1** As a visitor I want to register with email + password so I can check out and track orders.
- [ ] **US-3.2** As a registered shopper I want to log in and stay logged in across visits (JWT access + refresh).
- [ ] **US-3.3** As a shopper I want to manage my profile and delivery addresses.

### EPIC-4 · Cart
- [ ] **US-4.1** As a shopper I want to add/update/remove items so I can assemble an order.
- [ ] **US-4.2** As a logged-in shopper I want my cart persisted server-side so it survives across devices.
  - *Given* I'm logged in, *when* I add an item, *then* it appears in my server cart and the header count updates.

### EPIC-5 · Checkout
- [ ] **US-5.1** As a shopper I want to enter/choose a delivery address so the order ships correctly.
- [ ] **US-5.2** As a shopper I want to see shipping cost and total **before** paying so there are no surprises (directly targets the ~92% abandonment benchmark).
- [ ] **US-5.3** As a shopper I want to pay with a **mock/sandbox** method so I can complete an order in the demo.
  - *Given* I confirm, *then* a payment record with status `paid` (sandbox) is created and an order is generated.

### EPIC-6 · Orders
- [ ] **US-6.1** As a shopper I want to see my order history and order detail so I know what I bought and its status.

### EPIC-7 · Admin
- [x] **US-7.1** As an admin I want to view and update order status so I can process orders.
- [x] **US-7.2** As an admin I want inventory/stock control so I can avoid overselling.

---

## In scope vs out of scope

**In scope (Phase 1):** everything in the epics above, plus CI, automated tests, Docker Compose, and a live free-tier deployment.

**Explicitly out of scope (Phase 1):**
- Real payment capture, real shipping integration, tax calculation.
- Reviews, ratings, wishlist, promo codes, gift cards, loyalty.
- Recommendations / personalization (Phase 2).
- Multi-currency, multi-language, multi-warehouse.
- Native mobile apps.

**Deferred to Phase 2:** the data-engineering track (event capture → warehouse → dashboard), analytics, and any ML/recommendation work — deliberately sequenced *after* the store operates, mirroring how a real business adds a data function.

---

## Non-functional requirements

- [ ] **NFR-1 Performance** — API p95 latency < 400 ms for catalog reads (cached); storefront Largest Contentful Paint < 2.5 s on a mid-range mobile connection.
- [ ] **NFR-2 Accessibility** — WCAG 2.1 AA: keyboard navigable, visible focus, colour contrast ≥ 4.5:1, semantic landmarks, alt text on product images.
- [ ] **NFR-3 SEO** — server-rendered/ISR product and category pages; structured data (schema.org Product/Offer); sitemap.
- [ ] **NFR-4 Security** — password hashing (Django default), JWT with short-lived access tokens, HTTPS everywhere, OWASP Top 10 mitigations, no secrets in the repo.
- [ ] **NFR-5 Observability** — structured logs, request IDs, error tracking; health-check endpoint.
- [ ] **NFR-6 Maintainability** — typed code both sides (`basedpyright` / `tsc`), lint clean (`ruff`, ESLint), meaningful test coverage on domain logic and critical flows.
- [ ] **NFR-7 Reproducibility** — one-command local bring-up via Docker Compose; documented deploy steps.

---

## Release slices (traceability)

| Milestone | Epics covered | Demo at the end |
|---|---|---|
| M1 | EPIC-1, EPIC-2 | A browsable, searchable catalog |
| M2 | EPIC-3 | Accounts and auth flow |
| M3 | EPIC-4 | A working server-side cart |
| M4 | EPIC-5, EPIC-6 | A complete purchase (mock payment) |
| M5 | EPIC-7 | A manageable store |
| M6 | NFR pass | Hardened, tested, accessible |
| M7 | Deploy | A live, public demo |

See [`../04-delivery/ROADMAP.md`](../04-delivery/ROADMAP.md) for sequencing, dependencies, and risks.
