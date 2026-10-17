# Delivery Roadmap — LYSHEIM

> Consulted hats: **Senior Technical Lead** and **Senior Technical Project Manager**. Owner:
> Founder. Inputs: [`../PLAN.md`](../PLAN.md), [`../02-product/SCOPE.md`](../02-product/SCOPE.md),
> [`../03-architecture/ARCHITECTURE.md`](../03-architecture/ARCHITECTURE.md).
> Execution rules live in [`../WORKING-AGREEMENT.md`](../WORKING-AGREEMENT.md).
> Cadence: continuous increments, a compact change-log entry per increment, and a milestone
> retrospective at each gate
> ([`../decisions/ADR-0015-continuous-increments.md`](../decisions/ADR-0015-continuous-increments.md),
> [`../decisions/ADR-0016-lean-increment-ceremony.md`](../decisions/ADR-0016-lean-increment-ceremony.md)).

---

## 1. How to read this

Work is sliced into **milestones** (`M0`–`M8`) and, within each, into **increments** — each
increment is one small, demoable, committed step that passes every quality gate and carries
unit tests. An increment is the unit of the working agreement; a milestone is a
reviewer-visible capability.

Status legend: `[ ]` planned · `[~]` in progress · `[x]` done.

## 2. Milestone overview

| ID | Milestone | Outcome | Exit criteria | Status |
|---|---|---|---|---|
| M0 | Foundations | Both apps boot, gates wired, CI green | `docker compose up` runs API + web; CI passes | `[x]` |
| M1 | Catalog & browse | Products visible and navigable | Browse → PDP works with seeded data | `[x]` |
| M2 | Accounts & auth | Register/login works; the app is live | JWT flow + refresh exercised by tests; a public URL serves the catalog and auth | `[~]` |
| M3 | Cart | A cart a signed-in shopper can fill | Add/update/remove, stock-capped, behind the bearer token | `[x]` |
| M4 | Checkout & orders | Mock purchase end to end | Order created, paid, history shown | `[x]` |
| M6 | Hardening | Quality evidence produced | a11y/perf/security reports committed | `[x]` |
| M7 | Launch | Public demo hardened and finalised | Live URL passes a smoke journey; README published | `[x]` |
| M8 | Data track (Phase 2) | Analytics on real events | Funnel dashboard built on events | `[ ]` |

## 3. Milestone detail

### M0 — Foundations

- [x] `M0.1` Backend scaffold: `uv` project, Django 6, Django Ninja, settings split by env.
- [x] `M0.2` Frontend scaffold: Next.js (App Router, TypeScript strict), `pnpm`, design tokens → `globals.css`.
- [x] `M0.3` Root tooling: `ruff` + `basedpyright` (standard) config; ESLint + Prettier; `.editorconfig`.
- [x] `M0.4` Test harness: `pytest` (backend), `vitest` (frontend), one trivial test each.
- [x] `M0.5` `/healthz` endpoint + JSON logging + request-id middleware.
- [x] `M0.6` `.env.example`, `django-environ` wiring, secrets excluded from git.
- [x] `M0.7` `compose.yml` (Postgres + API + web) with a one-command start.
- [x] `M0.8` `seed` management command skeleton (idempotent, `--reset`).
- [x] `M0.9` GitHub Actions CI: path-filtered jobs for backend and frontend gates.
- [x] `M0.10` Tailwind CSS adopted; tokens declared in `@theme` (revises `M0.2`, `ADR-0013`).

### M1 — Catalog & browse

- [x] `M1.1` Catalog models + migrations (`Category`, `Product`, `ProductVariant`, `ProductImage`, `ImageCredit`).
- [x] `M1.2` Seed catalog: categories, products, variants, stock; curated images + credits vendored from `some_source/` (7 categories, 46 products).
- [x] `M1.3` Catalog read API (`/categories`, `/products`, `/products/{slug}`) + OpenAPI, with pagination, filters, and the error envelope.
- [x] `M1.4` Frontend API types generated from the committed OpenAPI snapshot (`frontend/openapi.json`), with a drift check in `Backend CI`.
- [x] `M1.5` Catalog listing page (grid, pagination, skeletons, empty state), partial-prerendered with the listing streamed behind a Suspense boundary.
- [x] `M1.6` Product detail page (gallery, price, availability, add-to-cart placeholder, per-product metadata); catalog cards now link to it.
- [x] `M1.7` Search, filter, and sort with shareable URL state — `?q=`, `?category=`, `?min_price=`, `?max_price=`, `?sort=`, `?page=`, carried through paging.
- [x] `M1.8` Home page (hero + featured), partial-prerendered: text hero in the shell, featured row streamed behind a Suspense boundary.
- [x] `M1.9` `/pages/credits` attribution page (`US-6.1`), reading a new public `/api/v1/credits` endpoint: every shipped image credited from the database, licence codes linked to their Creative Commons deeds.

### M2 — Accounts & auth

- [x] `M2.1` Custom `User` model + `Address` model + migrations; `django.contrib.auth` installed and `AUTH_USER_MODEL` swapped while the database still had no `auth_user` table.
- [x] `M2.2` Auth endpoints: register, login, refresh, logout, me (`ADR-0009`) — access token in the body, refresh token only as an httpOnly cookie scoped to the auth routes, with rotation and reuse detection.
- [x] `M2.3` Rate limiting on every auth endpoint (`US-2.2`, `NFR-3`) — keyed on the client rather than the account, so a limiter cannot be turned into a way to lock someone out of their own sign-in — with the limits themselves in settings, plus `ADR-0009`'s origin guard on `/auth/refresh`, which answers `403` before reading the cookie.
- [x] `M2.4` Frontend session: the access token in memory only, with one shared in-flight refresh so two concurrent calls cannot trip `ADR-0009`'s reuse detection and sign the customer out of everything; a three-state session (`restoring`/`authenticated`/`anonymous`) so a reload never flashes "signed out"; and the CORS configuration the browser needs, which had been missing entirely.
- [x] `M2.5` Login / register pages with validation.
- [x] `M2.6` Profile + addresses CRUD (API and UI) — ownership held by the query rather than a check after it, so another account's address is a `404` and not a `403` that would confirm the id exists; exactly one default while an account has any address, with `409` for clearing it; `/account` is one route with two sections, because `UX.md` gives one route, and it sends the restoring state rather than the signed-out one.
- [~] `M2.7` **Deploy the walking skeleton.** **Live:** Render runs the API from `backend/Dockerfile`
  with migrations and the seed on the boot path, Supabase holds the data, and the Vercel app serves
  the catalogue from it. Verified from outside the stack — `/healthz`, the 46 products over the
  public URL, `http` redirecting to `https`, the hardening headers, a `401` without a token, the
  refresh origin guard's `403`, CORS granted for the real origin and withheld from a foreign one (the check table is section 7.8). `RUNBOOK.md` section 7 is the
  procedure. Left: a sign-in through the live stack, which needs a browser — and the rate limit,
  which after the redeploy was measured again and still does not count the visitor: fifteen rapid
  attempts produced fifteen `401`s. The cause is narrowed from here — one `uvicorn` process, so the
  throttle's in-process cache is shared, and `prod.py` defaults the proxy count to 2 — which leaves
  the dashboard's own `NINJA_NUM_PROXIES` as the value to correct; `RUNBOOK.md` section 7.8 carries
  the action and the expected result. The correction is landed and pinned in the repository:
  `NINJA_NUM_PROXIES = 2` in `render.yaml`, the reasoning in `base.py`, and both wrong directions
  held by a test.

### M3 — Cart

- [x] `M3.1` `Cart` / `CartItem` models and API — get, add, update, remove, with server-side stock
  validation, behind the bearer token (`ADR-0017`; no guest cookie and no login merge, so the old
  guest-merge increment is deleted rather than deferred). One active cart per user by partial unique
  index, `PROTECT` on the variant so a withdrawal cannot empty a cart, `409` above stock, and a row
  lock so two concurrent adds cannot lose an increment. *(merges the old `M3.1` + `M3.2`)*
- [x] `M3.2` Cart UI: line items, quantity stepper, totals, empty state, and the sign-in gate
  `ADR-0017` puts in front of the first add. Read from a `lib/cart.ts` store that the header's count
  and the page both subscribe to, so an add updates both or neither; the stepper refuses above stock
  rather than reporting it afterwards. The product page gained the real add-to-cart (`US-3.1`) with a
  colour choice carrying each variant's own price, and the proceed-to-checkout action is the disabled
  placeholder `M4` replaces. *(renumbered from `M3.3`)*

### M4 — Checkout & orders

- [x] `M4.1` `Order` / `OrderItem` / `OrderEvent` models; guarded status transitions — with the
  product, variant and address **snapshotted** rather than referenced (`SET_NULL` where the cart uses
  `PROTECT`), the order's total and each line's arithmetic held by constraints, and the guard writing
  its audit event inside the same transaction that moves the status. *(no routes yet: `M4.2` and
  `M4.3` spend it)*
- [x] `M4.2` `/checkout/quote` (shipping options + totals) — the subtotal from the caller's cart plus
  every shipping option with the total it produces, behind the bearer token (`ADR-0017` corrects
  `API.md` §6's pre-reversal "optional"). It validates the address (a saved one through the caller's
  scope, an inline one against the address book's constraints) and leaves stock to `M4.3`'s
  transaction. Shipping is a fixed, flat, address-independent set (`ADR-0010`).
- [x] `M4.3` Idempotent order creation (`Idempotency-Key`) with stock decrement, plus the
  `PaymentGateway` port and its mock adapter with confirm/fail endpoints (`ADR-0010`) — the decrement
  is locked and conditional, inside the transaction that writes the order (`ADR-0017`), and
  `cancel_order` returns it so a decline cannot leak a reservation. `POST /orders` answers `201` on
  creation and `200` to a key it has already seen; the mock's two routes answer `404` unless
  `PAYMENT_PROVIDER=mock`.
  *(merges the old `M4.3` + `M4.4`)*
- [x] `M4.4` Order-confirmation email via the Tasks framework (mocked transport) — a `@task` enqueued
  once an order is `paid` and never on a decline, taking the order's **id** rather than the object so it
  would survive a real queue, and sending through a mailer that reaches no server (`locmem` in dev and
  tests, `dummy` in production so nothing accumulates).
- [x] `M4.5` Checkout UI: address → shipping → payment → confirmation — **one** `/checkout` route
  holding all four steps, because a half-finished order is not a page anyone can be linked to, reload
  into or share, so there is nothing for a URL to mean. The address step offers a saved address or the
  address book's own form; the shipping step renders the API's options with the total each produces;
  the payment step reviews the address and the total before either mock outcome (`US-4.3` asks for
  failure to be reachable rather than hoped for); and the confirmation reports the order's own status,
  which the capture decided. The cart's disabled "Proceed to checkout" is now a link to it — which was
  that control's stated reason for being disabled.
- [x] `M4.6` Order history and order-detail pages — `/orders` and `/orders/[number]`. Both read the
  caller's *own* orders, and that scope is the authorisation rather than a filter applied afterwards,
  so an order belonging to somebody else is not hidden here, it was never in the set — and the detail
  answers the same `404` for it as for a number that never existed, the refusal the address book
  already gives. The history answers with rows (a number, a date, a status, a count and a total) and
  the detail with the receipt the confirmation showed plus its `OrderEvent` timeline read forwards,
  because a status on its own says where an order is and not how it got there. The header's Orders
  entry and the checkout confirmation's "View your order" are the two ways in.

### M5 — Operator console

- [x] `M5.1` Django admin for the catalog and orders — list filters, search, inline images, guarded
  status transitions, and the audit visible. *(merges the old `M5.1` + `M5.2`)* — `M5.1a` landed the
  console itself and the catalog (`US-5.1`-`US-5.3`): the framework apps, middleware and template
  context processors, plus `accounts/admin.py` and `catalog/admin.py`. `M5.1b` landed the orders
  (`US-5.4`, `US-5.5`): a read-only receipt whose status moves only through actions, each calling the
  `transition_order` the API calls — and `cancel_order` for the one move that is also a stock event.
- [x] `M5.2` Operator runbook entry (create an `is_staff` operator; day-to-day actions) — `RUNBOOK.md`
  §9: making an operator, the `is_staff`-versus-`is_superuser` gap, signing in, the catalog work, and
  how an order moves.

### M6 — Hardening

- [x] `M6.1` Coverage push on the domain/service layer (≥ 80%) plus tests for edge cases — the gate is
  `pytest --cov`, with `fail_under = 80` and the measured scope declared in `backend/pyproject.toml`
  rather than in the workflow, so CI and a laptop enforce one number from one place (`RUNBOOK.md` §3).
  The 13 statements the baseline run found were refusals and `__str__` fallbacks, and each has a test
  now: the domain layer measures 100%.
- [x] `M6.2` Accessibility (axe on key routes) **and** performance (LCP budget, caching, image
  optimisation) pass → one combined report: [`../06-quality/A11Y-PERF-REPORT.md`](../06-quality/A11Y-PERF-REPORT.md).
  Two layers, because one would be the weaker claim: axe in **jsdom** over the components (22 tests,
  inside `pnpm test`, on every push) and axe in **Chromium** over 11 routes (`pnpm axe:audit`), which
  is the only layer that can decide colour — jsdom has no cascade, so it returns `color-contrast` as
  *incomplete* and a green component run is not a contrast claim. The first route run was 9 passing and
  2 failing on `link-in-text-block`: Tailwind's preflight gives an anchor the colour *and* the
  decoration of the text around it, so an unstyled `<Link>` with `hover:underline` is set apart by
  colour alone, which is what `1.4.1` forbids. Fixed by taking the `text-primary underline` the rest of
  the app already used. `NFR-1`'s third clause — "a documented JS bundle budget" — is now a number:
  **200 KiB** first-load against 148 KiB measured, next to `NFR-1`'s own 2.5 s LCP (668 ms for the
  listing, 1 112 ms for the PDP, on a throttled mobile profile) and its 300 ms catalog p95 (55 ms).
  `pnpm perf:audit` measures all of it; both audits are excluded from CI on purpose, and the report
  says which claims they do **not** cover. *(merges the old `M6.2` + `M6.3`)*
- [x] `M6.3` Security hardening (CSP, headers, throttles, secret guard, dependency audit) and the
  end-to-end error-envelope + request-id verification → [`../06-quality/SECURITY-REVIEW.md`](../06-quality/SECURITY-REVIEW.md).
  The increment's real find was that the console's sign-in had **no** limit on it at all: Ninja attaches
  throttles to Ninja operations, `/admin/login/` is a plain Django view, so every rule in the rate mapping
  stopped short of the one page where a guessed password buys every order in the system. The fix applies
  the same `LiveRateThrottle` from a middleware — keyed on the client rather than the submitted name,
  because keyed on the account it would be a way to lock a known operator out; counting only `POST`,
  because a refresh is not an attempt; and refusing with `Retry-After`. The policy turned out not to exist
  either: `SECURITY-BASELINE.md`, `PLAN.md` and `ARCHITECTURE.md` all call the CSP "a Django 6 built-in"
  and Django ships **no** CSP at all, so all three were corrected and the header is one middleware over
  one setting — with the console on a
  second, deliberately two-directive-wider policy, since its own templates carry inline `<script>`, and the
  narrowness held by a test that subtracting the two leaves exactly those directives. `manage.py
  check --deploy` under production settings reports **0 warnings and 1 error**, and the error is
  `mail.E001` on the mock transport `ADR-0010` chose; both dependency audits are clean and now *fail* a CI
  job rather than log to nobody. Verified in a browser as well as by header: `hydrated: true` and **zero**
  CSP violations on every route, which is the difference between "the header is set" and "the header does
  not break the app". Four deviations are recorded rather than hidden — `unsafe-inline` on `script-src`,
  the `dummy` mailer, a secret guard with no scanner beside it, and per-process rate windows.
  *(merges the old `M6.4` + `M6.5`)*
- [x] `M6.4` Observability: a failing task is visible in the logs — and the receiver this increment was
  meant to write **already exists, in Django**. The premise was that the `immediate` backend catches a
  task's exception onto its `TaskResult` instead of raising it, leaving a broken confirmation email
  silent "from both outside and in". Half of that holds and half does not. The request *is* green,
  which is right — a receipt is not worth a `500` after the card has been charged. The logs are not
  empty, though: `django.tasks.signals.log_task_finished` logs the failure at `ERROR` from the signal
  Django raises inside its own `except` block, with the traceback attached, and
  `config.settings.base` lets that logger reach the JSON console handler
  (`disable_existing_loggers: False`, root at `INFO`). A second receiver would have logged every
  failure twice, so what this increment adds is the proof rather than the code:
  `tests/test_order_email.py` fails the real task on purpose and asserts both the `ERROR` record and
  the traceback the caller's `TaskResult` carries. Corrected rather than quietly dropped — an
  increment whose premise is wrong is worth recording as wrong.

### M7 — Launch

`M7` is thin by design: `M2.7` already stood up the deploy, so this is the hardened, final one.

- [x] `M7.1` Production deploy — Render web, Supabase, Vercel; run migrations and
  seed the demo database. **It was already standing, and the push that closed `M6` had redeployed it**:
  `render.yaml` sets `autoDeployTrigger: commit`, so a push to `main` deploys the API, whose boot path
  runs `migrate` and the idempotent seed before `uvicorn`, and Vercel rebuilds the web app from the same
  push. So there was nothing to deploy and this increment became an audit of a deploy nobody had
  confirmed — and its first finding is that both hosts were *already* serving the hardened build:
  the live API answers with `M6.3`'s `Content-Security-Policy`, and the storefront with the widened
  two-directive policy the console gets instead.
- [x] `M7.2` Production smoke journey + keep-alive ping; finalise the runbook. The journey re-run end
  to end from outside — `/healthz`, 46 products over the public URL, `http` → `https`, `401` without a
  token, the refresh origin guard's `403`, a foreign-origin preflight that answers `200` and withholds
  every `access-control-allow-*` header, and nine routes answering `200` — and then the two audits
  **pointed at the deployed hosts** rather than at a local `next start`, which is what `A11Y_BASE_URL`
  was put there for: **17 of 17 pass in production**, 11 routes at WCAG 2.1 `AA`, LCP 1 508 ms
  (listing) and 1 720 ms (PDP) on the throttled mobile profile, 159 KiB of first-load JS, and a 48.6 ms
  catalog p95. Running them against the deploy is what turned up the third thing this milestone
  corrected: the image-cache assertion read `max-age`, and Vercel does not set a long one — it tells the
  browser `max-age=0, must-revalidate` and holds the optimised image in its **CDN**, where the evidence
  is a cache hit rather than a header. A check written for one host was failing a deploy that was
  honouring the same promise in the only way that host can. The ping is
  `.github/workflows/keepalive.yml` on a ten-minute schedule — and it begins with the next push to
  `main`, because a scheduled workflow runs from the default branch, which is noted here rather than
  assumed to have happened.
- [x] `M7.3` README with screenshots, architecture diagram, and the live URL. The README had gone
  stale — it still told a reader that checkout was unbuilt — so it was rewritten around what the app
  now does: 14 screenshots captured from a real session by `frontend/e2e/journey.spec.ts` rather than
  mocked up, the C4 container view, the measured quality numbers with their reports, and the
  deliberate limits with the ADR behind each. The console needed a spec of its own
  (`e2e/console.spec.ts`, `pnpm console:audit`), because it sits behind an operator account that the
  customer journey never has — so it **skips** unless credentials are supplied rather than inventing
  an operator, and CI keeps saying so.
  Two things the increment found on the way, and the second is why `M7` does not close here.
  `Idempotency-Key` was missing from `CORS_ALLOW_HEADERS`, so the browser refused the checkout
  `POST` at the preflight — the order read as a request that never happened rather than as a
  refusal. That one is fixed and local. **The other is open against the deploy:** pointed at the live
  hosts, the journey stops at sign-in, and the API says why — `POST /auth/refresh` answers **500**.
  The cause is the revision the deploy is running: `e24ba6a` still reads the replacement with
  `select_for_update().select_related("replaced_by")`, and Postgres refuses `FOR UPDATE` on the
  nullable side of that join (`NotSupportedError`, reproduced locally against Postgres). `fddd774`
  fixes it and is **committed but not pushed**, so production carries the broken revision and a
  session cannot survive a page load there. Until that push lands, `M7`'s exit criterion — the live
  URL passing a journey — is not met, and its §2 row stays `[~]` rather than being asserted. The same
  pass closed a type gate the deploy never sees: `replaced_by_id` on a self-referential FK trips
  `basedpyright` because the field is declared against the string `"self"` (`ADR-0014`'s gap, from the
  field side rather than the reverse one).
- [x] `M7.3a` The console had never had a stylesheet, and this is where that surfaced — asked, plainly,
  *why the admin is ugly*. Nothing served `/static/` at all: no `STATIC_ROOT`, no WhiteNoise, no
  `collectstatic` in the image, so every admin stylesheet had been a `404` since `M5.1` and the console
  rendered as bare HTML — in development too, because this project serves the API with `uvicorn` rather
  than `runserver`. It survived a milestone that screenshotted the console because unstyled HTML still
  behaves: the headings and tables render, the links work, every behavioural assertion passes, and the
  screenshots captured happily at 47 KB each where a styled one is 131 KB. Fixed with WhiteNoise, its
  two per-environment settings and a build-time `collectstatic`; asserted by
  `tests/test_console_static.py`; the console screenshots re-captured. `v0.1.60` has the measurement.

**`M7` closes here, and §2's row is `[x]` because both exit criteria were measured rather than
assumed.** The README is published. The live URL passes the journey: once `fddd774` and `4b9fe9e`
reached the hosts, `POST /auth/refresh` on the deploy answered `200` with an access token where it had
answered `500`, and `A11Y_BASE_URL=https://…vercel.app pnpm journey:audit` completed end to end in
21.5 s — register, cart, checkout, mock settlement, confirmation, and the order read back at
`/orders/<number>`. That is a browser driving the deployed stack, which is the check `M2.7` opened and
`M7.2` could only report as missing. One caveat is recorded rather than tidied away: `f3bf31a` — the
console's stylesheets — is committed and **not yet pushed** at the time of writing, so a reviewer who
opens the live `/admin/` before that push sees the unstyled console `M7.3a` describes. It changes no
exit criterion here, and it is the next push.

### M7.4 — The Spec Sheet (post-MVP, 2026-10-17)

The founder's review of the finished storefront was one sentence — *"the current UI/UX feels boring"*
— and this increment is the answer to it. It is the first work after `M7`, and it is deliberately
visual rather than functional: nothing in the API, the schema or the domain changed.

- [x] `M7.4` **A design direction, written down before it was coded.**
  [`../02-product/UX-DIRECTION.md`](../02-product/UX-DIRECTION.md) turns the feeling into seven named
  causes with files behind them — an empty hero, a type scale that stopped at `3rem`, one container
  width and one rhythm, uniform card chrome, an accent used too politely to see, **a tile that showed
  a name and a price while `material`, `color` and `in_stock` sat unused in the payload**, and no way
  into the catalogue from the header. The concept is "The Spec Sheet": the label is the identity, the
  display serif is the loud half of a loud/quiet field, and colour arrives in one saturated block per
  page instead of as a tint.
- [x] **Implemented as tokens, a tile, a hero and a spec table.** New type steps (`6xl`, `7xl`),
  `Fraunces` at one weight as `--font-display`, `h1`/`h2` in the display family site-wide; the tile
  gains the spec line (`Oak · Natural · In stock`), a square frame, a hairline rule and a
  display-size price; the home page gains a display hero and the terracotta band; the product page's
  existing `<dl>` becomes a ruled spec table; the header gains `Shop`. The skeleton was rebuilt to
  match the new tile, because a skeleton that is the wrong height is worse than none.
- [x] **Verified against every gate that existed before it.** 22 vitest files (four new assertions on
  the spec line, including the empty-material case), `tsc`/`eslint`/`prettier` clean, axe-clean on
  11/11 routes, LCP 740 ms and 1 092 ms against the 2 500 ms budget, first-load JS 147.8 KiB, p95
  49.8 ms, and the journey passing in 10.6 s with all eleven storefront screenshots re-captured from
  that run. The `NFR-1` risk of a second web font was measured rather than assumed: it cost nothing.
- [ ] **Not in this increment, and named so it is not mistaken for done:** motion, dark mode, reviews,
  wishlist, promo codes, and the "Room, not grid" concept — which needs an image budget before it can
  be built honestly (§5 of the direction document).

### M8 — Data track (Phase 2, deferred)

- [ ] `M8.x` Per `ARCHITECTURE.md` §9 and `_working/TODO_data-engineer.md`; ADRs written at the start of Phase 2.

## 4. Sequencing & dependencies

`M0 → M1 → M2 → M3 → M4 → M5 → M6 → M7`, then `M8`. Cart (M3) depends on Catalog (M1) and
Identity (M2); Checkout (M4) depends on Cart; Operator (M5) depends on Catalog and Orders.
`M2.7` deploys the walking skeleton as soon as auth works, so the catalog and sign-in are publicly
reachable from the middle of `M2` and every later increment lands on a live system. M6 hardens
everything already built, so it follows M5; M7 finalises that hardened build on the public URL.

## 5. RACI

Solo project: the Founder is Accountable for everything and is the sole decision-maker. The
`the_team/` hats are **Consulted**; the AI assistant is **Responsible** for producing
artifacts and code; the recruiter/client is **Informed** (reads the repo).

| Activity | Founder | Assistant | Hats | Reviewer |
|---|---|---|---|---|
| Plan / scope | A | R | C | I |
| Approve a stage gate | A/R | C | I | — |
| Write code + tests | A (review) | R | C | — |
| Commit (never push) | A (push) | R | — | I |
| QA scenarios / results | A | R (scenarios) | C | I |
| Deploy decision | A/R | C | C | I |

## 6. Definition of Done

- **Per increment:** see [`../WORKING-AGREEMENT.md`](../WORKING-AGREEMENT.md) §5.
- **Per milestone:** the milestone's exit criteria in §2 hold, its increments are all committed and green, and a short retrospective is appended to `CHANGE-LOG.md`.
- **v1:** the five evidence gates in [`../PLAN.md`](../PLAN.md) §2.

## 7. Change control

Any change to this roadmap follows `ADR-0002`: capture an ADR, append to
[`../CHANGE-LOG.md`](../CHANGE-LOG.md), and re-baseline [`../PLAN.md`](../PLAN.md). Scope
changes are the primary risk (`RISK-1`), so they are never made silently.

## 8. Risks

The full register is in [`RISK-REGISTER.md`](RISK-REGISTER.md).
