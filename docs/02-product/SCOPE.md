# Product Scope — LYSHEIM

> Consulted hats: **Senior Technical Project Manager** (lead), **Senior UI/UX**,
> **Senior Business Strategist**. Owner: Founder.
> Derived from [`../01-business/STRATEGY.md`](../01-business/STRATEGY.md) and
> [`../PLAN.md`](../PLAN.md).

---

## 1. Context

LYSHEIM v1 is a two-sided product:

- a **storefront** for shoppers, and
- an **operator console** for the person who runs the store.

It is delivered as a decoupled monorepo (Django API + Next.js web app) and scoped to what a
solo founder can ship, deploy, and keep polished. **Priority uses MoSCoW** (Must / Should /
Could / Won't-for-v1).

## 2. Personas

- [ ] **P-1 — The Renter (primary).** 25–35, urban, rents a small apartment, mobile-heavy
  shopper. **JTBD:** furnish a small space affordably without measuring mistakes or surprise
  shipping costs. **Pain:** high cart abandonment, distrust of big-ticket delivery.
- [ ] **P-2 — The Young Family.** 30–40, upgrading a home. **JTBD:** buy durable living and
  dining furniture with confidence. **Pain:** needs material/dimension clarity before buying.
- [ ] **P-3 — The Operator.** Runs the store day to day. **JTBD:** keep the catalog, stock,
  and orders correct without touching code.

> SEG-C (home-office buyers) is recognised in the strategy but is not a distinct v1 persona.

## 3. Epics

| Epic | Name | Milestone | Priority |
|---|---|---|---|
| `EPIC-1` | Catalog & browse | M1 | Must |
| `EPIC-2` | Accounts & auth | M2 | Must |
| `EPIC-3` | Cart | M3 | Must |
| `EPIC-4` | Checkout & orders | M4 | Must |
| `EPIC-5` | Operator console | M5 | Must |
| `EPIC-6` | Trust & content | M6 | Should |
| `EPIC-7` | Data & analytics | M8 (Phase 2) | Won't (v1) |

## 4. User stories & acceptance criteria

### EPIC-1 — Catalog & browse (M1)

- [ ] **US-1.1 Browse a category listing.** `Must`
  - AC: shows product image, name, price; paginated; a friendly empty state when a category
    has no products.
- [ ] **US-1.2 View a product detail page.** `Must`
  - AC: image gallery, price, description, availability, and an add-to-cart action; correct
    `<title>`/metadata.
- [ ] **US-1.3 Search products by keyword.** `Must`
  - AC: matches name and keyword; an explicit "no results" state with a recovery suggestion.
- [ ] **US-1.4 Filter and sort.** `Should`
  - AC: filter by category and price band, sort by price and newest; the URL reflects the
    filter state so results are shareable and back-button safe.
- [ ] **US-1.5 Home page with featured products.** `Should`
  - AC: hero plus a featured grid; fast LCP; primary CTA into the catalog.

### EPIC-2 — Accounts & auth (M2)

- [ ] **US-2.1 Register.** `Must` — AC: email + password with validation; duplicate-email error.
- [ ] **US-2.2 Log in.** `Must` — AC: issues a JWT access + refresh pair; clear error on bad
  credentials; endpoint is rate-limited.
- [ ] **US-2.3 Stay signed in / log out.** `Must` — AC: silent refresh of the access token;
  logout clears session state.
- [ ] **US-2.4 View and edit profile.** `Should` — AC: view and update display name.
- [ ] **US-2.5 Manage addresses.** `Should` — AC: create, edit, delete addresses with one
  default.

### EPIC-3 — Cart (M3)

- [ ] **US-3.1 Add to cart.** `Must` — AC: works for guests and signed-in users; immediate
  feedback; header cart count updates.
- [ ] **US-3.2 Update quantity.** `Must` — AC: respects available stock; rejects quantities
  above stock with a clear message.
- [ ] **US-3.3 Remove an item.** `Must` — AC: removes the line and recalculates totals.
- [ ] **US-3.4 View the cart.** `Must` — AC: line items, subtotal, estimated shipping, and a
  proceed-to-checkout action.
- [ ] **US-3.5 Persist the cart.** `Must` — AC: a signed-in cart persists across sessions; a
  guest cart merges on login.

### EPIC-4 — Checkout & orders (M4)

- [ ] **US-4.1 Provide a shipping address.** `Must` — AC: choose a saved address or enter a
  new one, with server-side validation.
- [ ] **US-4.2 Choose a shipping method (simulated).** `Must` — AC: options with cost; the
  order total updates.
- [ ] **US-4.3 Pay with the mock gateway.** `Must` — AC: a mock provider simulates success
  and failure; no real charge is made (see `ADR-0004` in the prior iteration's policy,
  re-affirmed at Stage 3).
- [ ] **US-4.4 Receive order confirmation.** `Must` — AC: an order number and summary; a
  confirmation email is dispatched via the Django Tasks framework (mocked transport).
- [ ] **US-4.5 View order history.** `Must` — AC: signed-in users see their past orders.
- [ ] **US-4.6 View order detail & status.** `Must` — AC: status badge, line items, shipping
  address, totals.

### EPIC-5 — Operator console (M5)

- [ ] **US-5.1 Manage categories.** `Must` — AC: create, edit, delete; slug is unique.
- [ ] **US-5.2 Manage products.** `Must` — AC: CRUD products, variants, images, and prices.
- [ ] **US-5.3 Manage inventory.** `Must` — AC: set stock levels; a low-stock indicator.
- [ ] **US-5.4 View and filter orders.** `Must` — AC: list orders and filter by status.
- [ ] **US-5.5 Update order status.** `Must` — AC: valid transitions only
  (`pending → paid → shipped → delivered`, or `cancelled`); changes are audited.

### EPIC-6 — Trust & content (M6)

- [ ] **US-6.1 Image credits / attribution page.** `Must` (licensing requirement)
  - AC: renders the attribution (creator, license, source URL) for every shipped image from
    the source manifest.
- [ ] **US-6.2 Shipping & returns page.** `Should`
- [ ] **US-6.3 About page.** `Should`

### EPIC-7 — Data & analytics (M8, Phase 2 — out of scope for v1)

- [ ] `US-7.1` Capture storefront events (view, add-to-cart, order) to a warehouse.
- [ ] `US-7.2` Build a conversion-funnel / abandonment dashboard.

## 5. In scope / out of scope (v1)

| In scope | Out of scope |
|---|---|
| Catalog, search, filter, sort | Multi-vendor marketplace |
| Server-side cart with guest merge | Real payment capture |
| Mock checkout and orders | Real logistics / shipping integrations |
| JWT accounts with addresses | Reviews, ratings, wishlist, promo codes |
| Operator console for catalog/stock/orders | Recommendations / personalization |
| Seeded demo data, deploy to free tier | Multi-currency, full i18n, native apps |

## 6. Non-functional requirements

- [ ] **NFR-1 Performance.** LCP < 2.5 s (p75, mobile) on catalog and PDP; API p95 < 300 ms
  for catalog reads; a documented JS bundle budget.
- [ ] **NFR-2 Accessibility.** WCAG 2.1 AA; axe-clean on key routes; fully keyboard
  operable; visible focus; text contrast ≥ 4.5:1.
- [ ] **NFR-3 Security.** Hashed passwords; short-lived access token + refresh; auth rate
  limiting; HTTPS only; no secrets in the repository; CSP enabled; dependency audit in CI.
- [ ] **NFR-4 Reliability.** A `/healthz` endpoint; a structured error envelope carrying a
  request id; idempotent seeding; documented database backup/restore.
- [ ] **NFR-5 Observability.** Structured JSON logs; correlation ids across API and web.
- [ ] **NFR-6 SEO.** Server-rendered catalog and PDP; per-page metadata; sitemap; semantic HTML.
- [ ] **NFR-7 Maintainability.** Typed (`basedpyright` standard, TypeScript strict), linted,
  and tested; backend domain/service coverage target ≥ 80%.
- [ ] **NFR-8 Cost.** Everything runs within the chosen free tiers.
- [ ] **NFR-9 i18n readiness.** English-only for v1, but no user-facing strings hard-coded in
  business logic.

## 7. Definition of Done (v1)

v1 is done when the five evidence gates in [`../PLAN.md`](../PLAN.md) §2 hold: it **runs**
(deployed, seeded, end-to-end), it **is engineered** (gates green, CI enforced), it **is
operated** (deploy, observability, security, a11y/perf budgets), it **is thought about**
(living docs + change history), and it **tells a story** (README with screenshots and a live
URL).

## 8. Open decisions → Stage 3 (architecture)

- **D1 — Operator console form.** Use **Django admin** for v1 (pragmatic, secure, fast,
  "boring tech") with a custom Next operator UI deferred to Phase 1.5, *or* build a bespoke
  Next console now. **Recommendation: Django admin for v1.**
- **D2 — Guest cart.** Cookie/session cart with server-side merge on login (recommended) vs
  sign-in-required cart.
- **D3 — Token storage.** httpOnly refresh cookie + in-memory access token (recommended) vs
  localStorage.
