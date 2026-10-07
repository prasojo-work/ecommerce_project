# Accessibility report — NORDVIK web client

| | |
|---|---|
| **Consulted hat** | Frontend / Accessibility |
| **Owner** | Founder |
| **Measured against** | commit `0adcca3`, plus the changes described here |
| **Tooling** | axe-core 4.14 (WCAG 2.1 A/AA + axe best-practice rules) driven over a headless Chrome, and Lighthouse's accessibility category |
| **Re-run with** | `node scripts/axe-audit.mjs` against a running production build |

## 1. Method

axe-core is the engine behind accessibility tooling; Lighthouse runs a **subset**
of its rules, so a clean Lighthouse score is not the same as an axe-clean page.
This audit therefore uses [`frontend/scripts/axe-audit.mjs`](../../frontend/scripts/axe-audit.mjs),
which injects axe-core 4.14 into a production build and runs the full tag set
(`wcag2a`, `wcag2aa`, `wcag21a`, `wcag21aa`, `best-practice`) over nine routes:

`/` · `/products` · `/products/{slug}` · `/cart` · `/checkout` · `/orders` ·
`/account` · `/login` · `/register`

It exits non-zero when anything is found, so it can gate CI later.

**Result: 0 violations across all nine routes.**

## 2. What was found and fixed

Three distinct defects. The first pass — which ran over six routes — found four
violations, one of them already fixed in source by the time it ran.

### 2.1 `link-in-text-block` — *serious* — cart, register (and four more routes)

Links sitting inside prose were distinguished from the surrounding text by
**colour alone** (`text-emerald-800 hover:underline`): "Please *sign in* to check
out.", "Your cart is empty. *Continue shopping*.". That fails WCAG 1.4.1 (Use of
Colour) for anyone who cannot perceive the difference — and the affordance was a
*hover* state, which does not exist on touch at all.

Fixed by making in-prose links permanently underlined
(`text-emerald-800 underline hover:text-emerald-900`). Because the same idiom was
copy-pasted around the app, it was fixed everywhere it appeared — cart, checkout,
orders, account, order detail and the shared auth form — rather than only on the
two routes the first pass happened to visit. Standalone links (main navigation,
pagination, card titles) were deliberately left alone: colour-only is not a
failure where the link *is* the block.

### 2.2 `heading-order` — *moderate* — the listing

`/products` rendered `<h1>Shop</h1>` and then every product title as an `<h3>`,
skipping a level. Anyone navigating by heading — a common screen-reader
technique — gets a broken outline that misrepresents the page structure.

Fixed by making the product card title an `<h2>`: it is a level-2 item beneath
the page's own heading. `ProductCard` has a single call site, so the change is
contained.

### 2.3 `landmark-unique` — *moderate* — the detail page

The detail page rendered two `<nav>` landmarks (the site navigation and the
breadcrumb trail) with no accessible names, so they were indistinguishable from
each other in a landmark list.

Fixed by naming each one: `Main` for the header navigation, plus `Breadcrumb` and
`Pagination` for the two the app adds.

## 3. What this audit does **not** cover

Stated plainly, because a clean automated score invites over-claiming:

1. **The manual keyboard pass.** `ARCHITECTURE.md` §9 pairs axe with a *manual
   keyboard pass*, and that is still outstanding. axe cannot tell whether every
   control is keyboard-reachable and operable, whether focus is always visible, or
   whether focus is managed sensibly after client-side navigation. It needs a
   human at a keyboard — recorded as an open item, not implied to be done.
2. **Signed-in views.** `/orders`, `/account` and `/checkout` were audited in
   their **signed-out** state, which is what an anonymous visitor receives. The
   authenticated states — address forms, the order table, the mock-payment form —
   are reached only with a session and belong to the E2E suite that is deferred.
3. **Screen-reader testing.** Nothing here substitutes for actually listening to
   NVDA or VoiceOver.
4. **Colour contrast** *is* covered: `color-contrast` is part of the AA tag set,
   and it is clean.

## 4. How to re-run

```bash
# terminal 1
cd frontend && pnpm build && pnpm start
# terminal 2
cd frontend && node scripts/axe-audit.mjs
```

Chrome comes from `CHROME_PATH`, or from a Playwright-managed Chromium when one
is installed on the machine.

## 5. Status against the non-functional target

| Attribute | Target | Status |
|---|---|---|
| Accessibility | WCAG 2.1 AA | **Automated checks clean** — axe 0 violations across 9 routes; Lighthouse accessibility 100 on all three audited routes. Manual keyboard pass **outstanding**. |
