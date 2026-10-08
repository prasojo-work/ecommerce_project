# Performance report — NORDVIK web client

| | |
|---|---|
| **Consulted hat** | Frontend / Performance |
| **Owner** | Founder |
| **Measured against** | commit `1aadc51`, plus the M6 changes described here |
| **Tooling** | Lighthouse CLI against a production build (`next build` → `next start`), Chrome from Playwright's managed Chromium |
| **Re-run with** | [`scripts/lighthouse-audit.sh`](../../scripts/lighthouse-audit.sh) |

## 1. Method, and what this does not cover

The three routes that matter were audited under Lighthouse's default mobile
preset (simulated 4G, 4× CPU throttling): the home page, the shop listing, and a
product detail page. Numbers come from a **production build**, not `next dev`.

**Tooling note.** The `web-perf` skill's workflow drives the Chrome DevTools MCP
server. That server is not configured in this environment, so the same
measurements were taken with the Lighthouse CLI instead — same engine, same
throttling, same thresholds. Only the report plumbing differs.

Not covered: real-user field data (there is no traffic yet — that arrives with
M7), large-catalogue behaviour (the seed has 10 products), and the operator
console, which is Django admin and not a public page.

## 2. Result

All three routes clear the M6 bar of **Lighthouse ≥ 90 on performance**, and every
category is now ≥ 96 — with **accessibility, best practices and SEO all at 100**.
Final state, after the performance pass, the accessibility pass and the
console-error fix in §4:

| Route | Performance | Accessibility | Best practices | SEO | LCP | TBT | CLS |
|---|---|---|---|---|---|---|---|
| `/` | 97 | 100 | 100 | 100 | 1.87 s | 180 ms | 0 |
| `/products` | 96 | 100 | 100 | 100 | 2.73 s | 100 ms | 0 |
| `/products/{slug}` | 96 | 100 | 100 | 100 | 2.58 s | 100 ms | 0 |

The LCP regression this pass set out to fix, measured as a controlled before/after
pair on the same pair of builds:

| Route | LCP | TBT | Speed Index |
|---|---|---|---|
| `/` | 1.77 s → 1.76 s | 220 ms → 190 ms | 0.78 s (unchanged) |
| `/products` | 2.74 s → **2.52 s** | 120 ms (unchanged) | 1.56 s → **0.77 s** |
| `/products/{slug}` | 3.03 s → **2.53 s** | 220 ms → **110 ms** | 1.50 s → **0.76 s** |

**Read the second table, not the absolute figures, for the effect of the fix.**
Lighthouse results vary between runs on this machine — LCP and the performance
figure especially, because the Next.js image optimiser caches downstream images
locally, so a later run measures a warm image cache rather than a cold one. A
third run put the detail route at 1.89 s against the 2.53 s above. The *deltas
within a matched pair* are the signal; any single absolute number is not.

## 3. What was changed

### 3.1 Catalog caching (`ADR-0013`)

The audit's structural finding was that the catalogue had no cache at any layer,
while `ARCHITECTURE.md` §9 promised a cached catalog path. The full reasoning is
in `ADR-0013`; the short version is that the shop route is dynamic by design (it
reads `searchParams`, and sets `force-dynamic`), so Next.js cannot route-cache it,
which leaves the API as the only layer that can serve it cheaply.

Measured on the API directly, against the seeded catalogue:

| Endpoint | First (cold) | Repeat (warm) |
|---|---|---|
| `GET /products?page_size=12` | 37.3 ms | **1.8 ms** |
| `GET /products/{slug}` | 26.1 ms | **1.7 ms** |

`catalog/test_cache.py` pins this harder than a stopwatch can: a repeat read of
the listing, the detail and the categories each assert **zero SQL queries**, and
three more tests assert that a create, an edit and a variant deactivation are all
visible on the *next* read rather than after the TTL.

### 3.2 LCP: preload the largest image

Both LCP misses had the same cause: the image that *is* the LCP was lazy-loaded.
`ProductGallery`'s main image and `ProductCard`'s first image had no `priority`
hint, so the browser only discovered them after CSS and hydration, and pictures
are served through the image optimiser with a round trip to the origin.

- `ProductGallery` now sets `priority={activeIndex === 0}` — the initial image is
  preloaded, and later gallery picks stay lazy, which is what we want for clicks.
- `ProductCard` takes an optional `priority` prop, and the listing passes it only
  for the first card.

Effect: detail LCP 3.03 s → **2.53 s** and Speed Index 1.50 s → **0.76 s**;
listing LCP 2.74 s → **2.52 s** and Speed Index 1.56 s → **0.77 s**; the detail
page's performance score went 91 → 97.

## 4. Findings, and where they stand

Recorded rather than silently dropped, in the same spirit as `SECURITY-REVIEW.md`.

1. **A guaranteed 401 on every anonymous page load — *fixed*.** The provider asked
   the API for a session on every mount, which for an anonymous visitor was a
   certain 401: one wasted request per page view (on the free tier, one that may
   also wake a sleeping API) plus a browser console error — the single item
   costing `best-practices` its last 4 points on all three audited routes.
   The fix is a **client-side session hint** (`nordvik.session` in
   `localStorage`): `"1"` after a sign-in or a successful restore, `"0"` after a
   definitive 401, and absent when this browser has never been asked. A first
   visit still probes once; every later visit skips the request entirely. A
   non-401 failure deliberately leaves the hint untouched, so a flaky connection
   cannot sign the user out of the UI.
   **This supersedes the marker-cookie fix recommended in the first version of
   this report, which could not have worked:** the refresh cookie is httpOnly
   *and* belongs to the API's origin (`127.0.0.1:8000` in development, a different
   domain in production), so client JavaScript can never read a cookie the API
   sets. Recorded, because the wrong recommendation is the instructive part.
   **Both halves proved necessary.** The client hint alone fixed repeat visits but
   not Lighthouse, which always measures a cold profile and so always saw the first
   visit's 401; the 204 alone still left a wasted request on every page view.
   Together, measured in a real browser: a fresh profile makes **one** request
   (`POST /auth/refresh` → `204`, preflight gone) with **no console error**, and
   every later visit makes none. `best-practices` went **96 → 100** on all three
   routes.
2. **Total Blocking Time of 110–190 ms.** This is React hydration of the
   application shell plus the header/cart providers, measured under 4× CPU
   throttling. It is inside the "good" band (< 200 ms) but leaves little room.
   Reducing it means shipping less JavaScript up front, which is a rendering
   change rather than a config tweak; not attempted here.
3. **27 KiB of unused JavaScript** (home) and **legacy-JavaScript polyfills**
   flagged on the same route. Modest, and Next's own bundle — nothing
   project-specific to trim.
4. **LCP is 2.52–2.53 s, just over the 2.5 s target.** The remaining cost is
   dominated by the remote `picsum.photos` demo images (an 800 ms fetch at the
   origin, outside our control) plus image-optimiser round trips. On real product
   imagery, served from the same origin and correctly sized, this should fall well
   under. The preload work is what was ours to fix.
5. **`/products` accessibility is 98, not 100** — "heading elements are not in a
   sequentially-descending order". Handled in the accessibility pass, not here.

## 5. Non-functional targets (`ARCHITECTURE.md` §9)

| Attribute | Target | Status |
|---|---|---|
| Latency | API p95 < 400 ms (catalog, cached) | **Met.** 1.8 ms warm / 37 ms cold, measured locally |
| Latency | LCP < 2.5 s | **Marginal** — 1.76 s home; 2.52–2.53 s on the two image-led routes |
| Accessibility | WCAG 2.1 AA | Audit in progress; Lighthouse a11y 98–100 so far |

Performance is **not** the current bottleneck. The API answers in single-digit
milliseconds when warm, CLS is 0 everywhere, and every score is ≥ 90. The honest
summary is that the images and the session-restore request are what is left.
