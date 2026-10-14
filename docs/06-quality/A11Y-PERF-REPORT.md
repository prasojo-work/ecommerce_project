# Accessibility & Performance Report — LYSHEIM

> Consulted hats: **Senior UI/UX** and **Senior Frontend**. Owner: Founder.
> Status: **measured**. Every figure below was produced on 2026-10-14 against a production build
> (`pnpm build`, then `pnpm start`) with the seeded local API behind it, and §2 carries the commands,
> so a reader can reproduce the numbers instead of taking them on trust. This is the combined report
> `M6.2` asks for; `NFR-2` and `NFR-1` ([`../02-product/SCOPE.md`](../02-product/SCOPE.md) §6) are the
> requirements it answers.

---

## 1. What this report claims, and what it does not

### 1.1 Two layers, because one alone would be a weaker claim than it looks

Accessibility is measured twice, and the two measurements are not redundant.

| Layer | Where it runs | Tool | What it can decide |
|---|---|---|---|
| Component | `src/**/*.test.tsx` | `axe-core` in **jsdom** | Roles, accessible names, labels, ARIA wiring, heading order, form semantics — for one component in isolation |
| Route | `e2e/a11y.spec.ts` | `axe-core` in **Chromium** | All of the above, plus computed styles: colour contrast, target size, landmark structure, and the accessibility tree of a composed page |

The component layer is the cheap one: it runs inside `pnpm test`, on every push, with no browser and
no stack. The route layer is the expensive one, and it is deliberately **not** in CI — `frontend.yml`
builds partial-prerendered shells with nothing serving `NEXT_PUBLIC_API_BASE_URL`, and adding Postgres
and Python to that job would be a large amount of CI to prove something about composed markup. It is a
documented command run at the milestone, which is what it is here for.

What the component layer **cannot** do is colour. jsdom has no layout engine and no cascade, so axe's
`color-contrast` rule cannot resolve a pair of computed colours; it returns `incomplete`, and
`toHaveNoViolations` only ever reads `violations`. A green component run is therefore **not** a
contrast claim. Contrast is measured in the browser layer, and only there. Both runners are scoped to
the same four tags (`wcag2a`, `wcag2aa`, `wcag21a`, `wcag21aa`); axe's `best-practice` set is excluded
in both, so a red test means "this breaks WCAG 2.1 AA" rather than "somebody would prefer otherwise".

### 1.2 What is not covered, stated plainly

- **Authenticated routes.** A filled cart, checkout, an order confirmation and the two order pages all
  need a session, and the refresh cookie is `Lax` rather than `Secure` locally, so auditing them is a
  separate job rather than a `beforeAll` hook pretending to be one. The signed-out shells of those
  routes *are* audited.
- **Keyboard traversal, focus order and visible focus.** No axe rule decides whether focus is
  *visible*, whether the order is sensible, or whether a widget can be left with the keyboard. `NFR-2`
  asks for these; they are not machine-checked here, and calling this report "WCAG 2.1 AA" on their
  behalf would be overclaiming. They are reviewed by hand at `M7`.
- **Screen-reader flow.** Roles and names are checked; the experience of moving through the page with
  a screen reader is not.
- **Field LCP.** §4.2 explains why a loopback number is a regression gate and not a field measurement.

## 2. How to reproduce

Prerequisites: Postgres up, migrations applied and the catalog seeded, the API running, and a
production build of the web app.

```bash
cd backend
uv run python manage.py migrate && uv run python manage.py seed
uv run uvicorn config.asgi:application --host 127.0.0.1 --port 8000

cd ../frontend
pnpm build && pnpm start

pnpm audit:routes # both route audits
pnpm axe:audit    # accessibility only  (e2e/a11y.spec.ts)
pnpm perf:audit   # performance only    (e2e/perf.spec.ts)
pnpm test         # the component layer, no stack required
```

The combined script is `audit:routes` and not `audit` on purpose: `pnpm audit` is pnpm's own
dependency check, and `SECURITY-BASELINE.md` calls it for exactly that. A script of the same name
would have shadowed a security command with an accessibility one.

`A11Y_BASE_URL` retargets both audits at a deployed environment and `PERF_API_URL` retargets the API
the perf spec reads, so the same specs can be pointed at the live URL at `M7` without an edit.
`playwright.config.ts` runs a single worker with retries off: a flake here is a finding, not noise to
be smoothed over.

## 3. Accessibility — results

### 3.1 Component layer: 22 tests, 6 files, all passing

| File | Tests | What it pins |
|---|---|---|
| `src/components/product-card.test.tsx` | 5 | The card's link name, heading level, image alt |
| `src/components/pagination.test.tsx` | 5 | `nav` landmark, page links, current-page marking |
| `src/components/text-field.test.tsx` | 4 | Label association and error announcement, with and without an error |
| `src/components/empty-state.test.tsx` | 3 | Both variants |
| `src/components/product-gallery.test.tsx` | 3 | Thumbnail buttons and the selected state |
| `src/test/a11y-harness.test.tsx` | 2 | That the harness itself reports a violation it is handed |

The last row is there because a harness that silently passes everything looks exactly like a clean
codebase. It renders markup with a known violation and asserts the runner finds it.

The suite as a whole is 22 files and 163 tests, all green.

### 3.2 Route layer: 11 routes, all passing

Audited at a 390 × 844 viewport against the production build, each route asserted to have **no**
WCAG 2.1 A/AA violation:

`/` · `/products` · `/products?q=chair&sort=-price` · `/products/{slug}` · `/pages/credits` · `/login` ·
`/register` · `/cart` · `/checkout` · `/orders` · `/account`

The product-detail route asks the API which slug to use rather than hard-coding one, so a renamed
product cannot silently turn the audit into a check of Next's not-found page.

### 3.3 The finding: `link-in-text-block` on two routes

The first run was **9 passing, 2 failing** — `/pages/credits` and `/register`, both on the same
serious rule, `link-in-text-block` (WCAG 1.4.1, *Use of Color*). Forty-six pairs of links on the
credits list and one on the registration form were set apart from the sentence around them by colour
alone.

**The cause is a Tailwind default, not a mistake anyone made in a component.** Preflight gives every
anchor `color: inherit; text-decoration: inherit`, so an unstyled `<Link>` inside a paragraph takes the
colour *and* the underline of the text next to it. The credits links asked for `hover:underline`, which
by definition is not there in the state a reader is reading in.

**The fix was to follow the house style that already existed.** Every other inline link in the app —
`add-to-cart-button.tsx`, the checkout confirmation, the order detail — is `text-primary underline`.
The credits links became `text-primary underline underline-offset-4`, and the two auth-form links
picked up the same classes. Ten lines across two files, no new abstraction.

**Worth recording: `/login` passed the audit with the identical defect.** The same component renders
both forms, and at the moment of audit the sign-in page's link was not reported. axe decides whether a
link sits "in a block of text" partly by how much of the block the link is, and "Create an account"
(17 of 27 characters) crosses that line where "Sign in" (7 of 32) does not. So the pass was luck, and
the fix was applied to both branches of that component rather than to the one axe objected to. A rule
that is right for the wrong reason is still right, and a fix that only satisfies the checker would have
left the login page wrong.

### 3.4 Contrast

Measured in the browser, where it can be. No contrast violation is reported on any audited route, so
every text/background pair on those eleven pages clears the 4.5:1 that `NFR-2` names. This is the one
claim in this report that the component layer could not have made.

## 4. Performance — results

### 4.1 The conditions, and why they are hand-rolled

`NFR-1` names p75 **mobile**, so the profile is Lighthouse's mobile preset, driven through the
protocol the browser already exposes:

- viewport 390 × 844;
- `Emulation.setCPUThrottlingRate` at 4×;
- `Network.emulateNetworkConditions` at 150 ms RTT, 1.6 Mbps down, 750 Kbps up.

Hand-rolled rather than a Lighthouse run because the number must be reproducible by anyone with this
repository and nothing else installed. These are the same two primitives Lighthouse uses, so the
conditions are honest about what they claim.

### 4.2 LCP

| Route | LCP | Budget | Headroom |
|---|---|---|---|
| `/products` | 668 ms, 704 ms (two runs) | 2 500 ms | ~3.6× |
| `/products/{slug}` | 1 112 ms | 2 500 ms | ~2.2× |

The PDP is the slower of the two, which is the expected shape: the listing's shell carries the hero and
the grid streams behind its Suspense boundary, while the detail page waits on one product's gallery.

**What this number is and is not.** The API is on loopback, there is no TLS hop and no CDN, so this
measures how much work the app does before it paints — a **regression gate**, which is what `M6.2`
needs. It is not the p75 a shopper on a train experiences; that is a field measurement, it comes from
real traffic on the deployed URL, and it belongs to `M7`. Reporting 668 ms as `NFR-1` met would be
reading the requirement more loosely than it is written.

The spec waits for the LCP to hold still rather than for `load` to fire, because on a
partial-prerendered route the candidate can still be replaced after `load` — measuring the first thing
that appeared instead of the page that finished would flatter it.

### 4.3 First-load JS — the budget `NFR-1` asked to be documented

`NFR-1`'s third clause is "a documented JS bundle budget", and until this increment there was none.
There is now: **200 KiB of first-load JavaScript per route**, measured as the sum of `transferSize` for
every script the browser actually fetched, counted in a fresh context so nothing is served from cache.

| Route | Measured | Budget |
|---|---|---|
| `/products` | 147.8 KiB | 200 KiB |
| `/products/{slug}` | 148.3 KiB | 200 KiB |

Roughly a third of headroom over the measurement. The reasoning is that a budget an order of magnitude
clear of the real number passes a regression that *doubles* the bundle, which is the opposite of a
gate; a third of headroom lets a new dependency land without an argument while a doubling still trips.
Changing it is a decision, and this section is where it gets argued.

### 4.4 API p95 for catalog reads

| Measurement | Budget |
|---|---|
| 55.5 ms, 50.6 ms (two runs, n = 24) | 300 ms |

Taken as the nearest rank over 24 sequential requests to `/api/v1/products?page_size=12` — no
interpolation, because with 24 samples an interpolated percentile would invent a request that was never
made. This includes client-side round-trip overhead, so the server's own share is smaller than the
figure shown.

### 4.5 Caching and image optimisation

Asserted rather than eyeballed, so a regression is caught:

| Evidence | Observed |
|---|---|
| Hashed JS chunk | `cache-control: public, max-age=31536000, immutable` |
| Optimised image (`w=640`), self-hosted | `content-type: image/webp`, `public, max-age=14400, must-revalidate`, 20 676 bytes |
| Optimised image (`w=640`), on Vercel | the same bytes and the same format, but `public, max-age=0, must-revalidate` with `x-vercel-cache: HIT` — the CDN holds it rather than the browser (§7) |
| Image markup | `next/image` on every shipped image, with a `srcset` from 256w to 3840w at `q=75` |

The image request is made with a browser's `accept` header, because the optimizer negotiates on it — a
request without one gets a JPEG and would have made the format look worse than it is. Every image in
the app already carries a `sizes` attribute (`product-card.tsx`, `product-gallery.tsx`,
`cart-screen.tsx`), which is what stops a card in a three-column grid from fetching a candidate sized
for the whole viewport; the audit asserts the markup, not that intent.

## 5. Where the budgets live, and how to change one

| Budget | Value | Declared in | Set by |
|---|---|---|---|
| LCP | 2 500 ms | `e2e/perf.spec.ts` | `SCOPE.md` `NFR-1` |
| API p95, catalog reads | 300 ms | `e2e/perf.spec.ts` | `SCOPE.md` `NFR-1` |
| First-load JS | 200 KiB | `e2e/perf.spec.ts` | this report, §4.3 |
| WCAG level | 2.1 A + AA | `src/test/axe.ts`, `e2e/a11y.spec.ts` | `SCOPE.md` `NFR-2` |

One constant object and one tag list, each read by both layers where it applies, so the numbers cannot
drift between the component runner and the browser runner.

## 6. Evidence summary

| Gate | Command | Result |
|---|---|---|
| Component accessibility | `pnpm test` | 163 tests, 22 files, pass |
| Route accessibility | `pnpm axe:audit` | 11 routes, 0 WCAG 2.1 A/AA violations |
| LCP, mobile profile | `pnpm perf:audit` | 668/704 ms and 1 112 ms against 2 500 ms |
| First-load JS | `pnpm perf:audit` | 147.8 / 148.3 KiB against 200 KiB |
| Catalog p95 | `pnpm perf:audit` | 55.5 / 50.6 ms against 300 ms |
| Caching, images | `pnpm perf:audit` | immutable chunks, `webp` at 4 h |

**Where this stands.** These budgets were re-measured after `M6.3` put a `Content-Security-Policy` on the
storefront, and all 17 assertions pass again with it in force. The other two `M6` increments are closed:
`M6.3` (security hardening, the console throttle, and the end-to-end error-envelope + request-id
verification) is [`SECURITY-REVIEW.md`](SECURITY-REVIEW.md), and `M6.4` turned out to need no receiver —
Django already logs a failed task, and `tests/test_order_email.py` holds that now.

## 7. Production verification (`M7.2`, 2026-10-14)

Both gates were re-run against the deployed hosts rather than a local `next start`, because they are
only evidence about the environment they are pointed at — and `A11Y_BASE_URL` exists so that they can
be:

```
A11Y_BASE_URL=https://ecommerce-project-five-psi.vercel.app pnpm audit:routes
```

`17 passed` — the same 11 routes at WCAG 2.1 `AA` and the same six performance budgets, on the public
build rather than on a laptop:

| Gate | Local (§6) | Deployed | The promise |
|---|---|---|---|
| Route accessibility | 11 routes, 0 violations | 11 routes, 0 violations | `NFR-2` |
| LCP | 668 / 1 112 ms | 1 508 / 1 720 ms | `NFR-1`'s 2 500 ms |
| First-load JS | 147.8 / 148.3 KiB | 159.2 / 158.0 KiB | 200 KiB |
| Catalog p95 | 55.5 / 50.6 ms | 48.6 ms | `NFR-1`'s 300 ms |

The larger LCP is the network and not a regression — the deployed run is throttled mobile (4× CPU,
Slow 4G) over a real connection rather than over loopback — and it still lands at 60-69% of the budget.

**Confronting the deploy changed exactly one assertion, and it is worth recording why.** The image
check in §4.5 read `max-age` and demanded at least an hour. That is true self-hosted — `next start`
answers with `cache-control: public, max-age=14400, must-revalidate` — and false on Vercel, which tells
the browser `max-age=0, must-revalidate` and holds the optimised image in its **CDN**, where the
evidence is `x-vercel-cache: HIT` on a repeat request rather than a number in a header. The check was
therefore failing a deploy that was honouring the same promise by the only means that host offers. It
now branches on whether a CDN header is present: with one, it proves the cache hit; without one, it
proves the `max-age`. Both branches pass where each was written — CDN `HIT` in production,
`max-age=14400` locally — which is a small change and a general lesson. An audit is evidence about the
environment it was written in, and pointing it somewhere else is how that gets found out.
