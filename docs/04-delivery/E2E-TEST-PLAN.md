# End-to-End Test Plan — NORDVIK

> Consulted hats: **QA**, **Technical Lead**, **Frontend**, **Cloud Engineer**.
> Status: **Planned — deferred until the MVP feature set is frozen (after M5).**
> Owner when executed: **M6 — Hardening**. Tracking: [`ROADMAP.md`](ROADMAP.md#deferred-workstreams).

---

## 1. Why this is deferred

Browser automation is the most expensive test layer per assertion and the one most prone to
flaking. Building it before the feature set stops moving means rewriting the suite every
milestone. The plan below is therefore recorded now, executed later.

**Trigger to start:** M1–M5 are complete and the MVP feature set is frozen.
**Blocking prerequisites:** two pieces of missing infrastructure, listed in §4. Neither should be
built for the sake of E2E alone — the seed command earns its keep in local development and demos.

`ARCHITECTURE.md` §11 already commits to "Vitest + Playwright for critical flows"; this document is
that commitment made concrete. It is a *clarification* of existing scope, not new scope.

## 2. Principles

1. **Test pyramid discipline.** E2E proves the browser boundary works end to end. It must **not**
   re-assert rules already covered faster and more precisely below it.
2. **Black-box only.** The suite drives a running stack over HTTP and the DOM. It never imports
   application code, and it lives outside both app directories.
3. **Semantics-first selectors.** `getByRole`, `getByLabel`, `getByText`. This keeps the suite
   coupled to what a user perceives and doubles as a WCAG 2.1 AA smoke test — the target in
   `ARCHITECTURE.md` §9. A `data-testid` is a last resort and must be justified in review.
4. **Deterministic data.** No test may depend on rows another test created, or on timestamps.
5. **Failures must be diagnosable.** Trace, screenshot and video on first retry, retained as CI
   artifacts.

## 3. Scope — the critical journeys

Priority: `P1` = blocks the milestone, `P2` = valuable, first to cut if time is short.

| ID | Journey | Steps | Key assertions | Pri |
|---|---|---|---|---|
| `E2E-1` | Browse and find a product | Home → category → sort by price → product detail | Products listed; sort order actually changes the first result; detail shows price, variants, stock | P1 |
| `E2E-2` | Search and filter | `/products?q=` → apply category filter → clear | Matching results only; empty state renders when nothing matches | P1 |
| `E2E-3` | Auth gate on cart | Anonymous → product → add to cart | Redirected to `/login`; cart is not silently mutated | P1 |
| `E2E-4` | Register, session and logout | Register → reload → logout → reload | Session survives a full page reload (refresh-cookie rotation); logout clears the header and the cart badge | P1 |
| `E2E-5` | Address book | Account → add address → set default → remove | Address persists across reload; exactly one default | P1 |
| `E2E-6` | **The full purchase** | Login → add 2 items → cart → checkout → pick address → pick express → pay | Running total equals subtotal + express cost; lands on order confirmation; order shows `Paid`; cart is now empty | P1 |
| `E2E-7` | Free-delivery threshold | Cart just below threshold → cross it at checkout | Shipping flips to "Free" exactly at Rp 500.000 | P2 |
| `E2E-8` | Declined payment and retry | Checkout with "simulate a declined payment" → land on order page → retry | Order sits at `Awaiting payment`; retry takes it to `Paid`; only one order exists | P1 |
| `E2E-9` | Duplicate-submit guard | Double-click Pay | Exactly one order in history, not two | P1 |
| `E2E-10` | Stock guard | Add more than available → checkout | Clear, actionable error; no order created; stock unchanged | P1 |
| `E2E-11` | Customer isolation | User B opens User A's order URL | "Order not found", never A's data | P1 |
| `E2E-12` | Order history and detail | Account → orders list → open detail | Newest first; snapshots match what was bought even after a catalog edit | P1 |
| `E2E-13` | Admin manages catalog *(after M5)* | Admin → create product + variant → publish | Product is purchasable in the storefront without a deploy | P1 |
| `E2E-14` | Admin advances an order *(after M5)* | Admin → move order to `shipped` | Customer's order page reflects the new status | P1 |
| `E2E-15` | Mobile viewport | Run `E2E-1`, `E2E-5`, `E2E-6` on a 390×844 project | No horizontal overflow; primary action reachable without zoom | P2 |
| `E2E-16` | Accessibility smoke | `@axe-core/playwright` on home, catalog, product, cart, checkout, orders | Zero serious/critical violations | P2 |

## 4. Blocking prerequisites

Build these **before** writing the first spec.

- [ ] **Seed command.** `python manage.py seed_demo` — idempotent, deterministic: categories,
      products, variants with known `sku` and **explicit** stock levels, plus a demo customer and
      a demo admin. E2E asserts against these known values, so the data contract must be stable
      and documented in the command's `--help`. Today there is no seeding mechanism at all.
- [ ] **Isolated, resettable database.** E2E must never touch development data. Use a separate
      compose project name and database (e.g. `nordvik_e2e`), recreated per run, with
      `seed_demo` run immediately after `migrate`.
- [ ] **A documented "stack up + wait for healthy" step.** The suite needs `db` → `api` → `web`
      ready, and must wait on `GET /health` rather than a fixed sleep.

## 5. Environment and orchestration

- `docker compose up -d db api web` brings up the stack; the suite runs against
  **`http://localhost:3000`**. Tests use the *browser* URL path, never the internal one.
- **Build-time URL gotcha:** `NEXT_PUBLIC_API_URL` is inlined into the bundle at build time. The
  image under test must be built with the URL the browser can reach (`http://localhost:8000/api/v1`),
  not the internal `http://api:8000/api/v1` used for server-side rendering. Getting this wrong
  produces a suite that fails with opaque CORS/network errors.
- **Cookies:** the refresh token is an httpOnly cookie scoped to `/api/v1/auth`. With
  `DJANGO_DEBUG=true` it is not `Secure`, so http-localhost works. If a future config sets
  `Secure`, the suite must run over HTTPS or the session-persistence tests (`E2E-4`) will fail.
- **CORS:** `CORS_ALLOWED_ORIGINS` must include the frontend origin — it already does.

## 6. Layout and tooling

```
e2e/                        # new top-level workspace — black-box, drives the running stack
  playwright.config.ts      # projects: chromium-desktop, mobile-chrome
  fixtures/                 # users, addresses, seeded-catalog reference data
  pages/                    # page objects: thin, intent-revealing
  specs/                    # one file per journey in §3
```

- `@playwright/test`, TypeScript, `webServer` **not** used for the API (compose owns it).
- Page objects expose intent (`checkout.payWith("express")`), never raw selectors. Assertions stay
  in specs so a failure message names the behaviour, not the DOM.
- A `pnpm e2e` script (and a root `make e2e`) so the suite is one command, as `compose.yml` intends.

## 7. Reliability policy (anti-flake)

- No `waitForTimeout`. Ever. Playwright's auto-waiting `expect` assertions only.
- Parallel-safe: **every test registers its own user** with a unique email rather than sharing one,
  so `fullyParallel` needs no cross-test locking.
- Any test that needs catalog state *modified* restores it, or is marked serial with a comment
  explaining why.
- `retries: 1` in CI, `0` locally — a retry that passes is a **flake to fix**, and the CI job must
  be able to tell you which tests needed a retry.
- Budget: whole suite under ~5 minutes wall clock. Above that, move work down the pyramid.

## 8. CI integration

Add a third job to [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) after `backend`
and `frontend`, so a broken build fails before the expensive browser run:

- postgres service container (same image/env as the backend job);
- `uv sync` → `migrate` → `seed_demo` → start the API;
- `pnpm install` → `pnpm build` → start the web server;
- wait for `/health`, then `pnpm e2e`;
- upload `playwright-report/` and `test-results/` (traces) on failure;
- gated on main and PRs alike.

## 9. Explicit non-goals

- **Pricing, stock arithmetic, idempotency semantics, permission scoping** — covered with far better
  precision by the pytest suites. Do not duplicate them here.
- **Load and soak testing** — separate concern (`k6`/Locust) in the M6 NFR pass.
- **Visual regression** — tempting, but a screenshot baseline on an in-flux UI is a flake factory.
  Revisit after the UI freezes.
- **Cross-browser matrix** — Chromium desktop + one mobile viewport only. Firefox/WebKit only if a
  real bug justifies it.
- **Real payments** — out of scope by `ADR-0004`; the mock path is what `E2E-6`/`E2E-8` exercise.

## 10. Exit criteria

- [ ] All `P1` journeys green on CI, and green on **three consecutive runs** with `retries: 1`.
- [ ] Zero tests requiring a retry on a clean run.
- [ ] Traces uploaded and readable for a deliberately broken build (verify by breaking one selector).
- [ ] `pnpm e2e` documented in `README.md` with the runbook (bring stack up, seed, run, tear down).
- [ ] Suite completes in under ~5 minutes.
- [ ] No `data-testid` added without a review comment justifying it.

## 11. Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Flake erodes trust in the suite | High | §7 policy; retry count is treated as a metric, not noise |
| Tests coupled to CSS/class names | Medium | §2 semantics-first selectors; page objects |
| Seed data drifts from assertions | Medium | Seed values documented in `--help`; fixtures import them |
| Wrong API URL baked into the build | High | §5 explicit gotcha; assert `/health` reachability before specs run |
| Suite slow enough to be skipped | Medium | ~5 minute budget; keep work in lower layers |
| E2E written *before* the UI freezes | High | This document is deferred until after M5 by design |

## 12. Execution checklist (for when the trigger fires)

- [ ] Build the three prerequisites in §4.
- [ ] Add the `e2e/` workspace and `playwright.config.ts` with both projects.
- [ ] Write `E2E-6` (full purchase) first — it proves the harness end to end.
- [ ] Add the CI job (§8) once three journeys are green locally.
- [ ] Fill in the remaining `P1` journeys, then `P2`.
- [ ] Walk §10 and close it out in the M6 hardening report.

## 13. Open questions for the founder

1. **Guest vs logged-in checkout.** `SCOPE.md` has no guest-checkout story and orders require auth,
   so `E2E-3` asserts the *redirect*. Confirm that is intended, or this becomes a feature request.
2. **Should admin journeys be E2E or API-level?** Depends on the M5 delivery choice (§M5): a Django
   admin UI can be smoke-tested cheaply, whereas a bespoke admin frontend deserves full `E2E-13`/14.
3. **Mobile project scope.** `UX.md` is "mobile-first"; is one 390 px viewport enough, or do we want
   a real device profile (iPhone 14 / Pixel 7)?
