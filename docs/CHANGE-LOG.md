# Change Log

> **Append-only.** Never rewrite the past. Newest entry at the top of *History*.
> This file records every change to the agreed plan, with its rationale. The current truth
> lives in [`PLAN.md`](PLAN.md); this file records how we got there.

## History

### 2026-10-10 — v0.1.19 — M1.6 product detail page

**Context.** `M1.6`. `US-1.2` fixes the content — image gallery, price, description, availability,
and an add-to-cart action, with correct `<title>`/metadata. `UX.md` section 5 gives the PDP a
skeleton for loading and "n/a (404 page)" for empty.

**What changed.**

- `app/products/[slug]/page.tsx` — the gallery beside price, availability, description, material,
  colour and dimensions, with per-product `generateMetadata` (`NFR-6`).
- `app/products/[slug]/not-found.tsx` — what a withdrawn or mistyped slug gets.
- `components/` — `ProductGallery`, `AddToCartButton`, `ProductDetailSkeleton`.
- `lib/dimensions.ts` — labelled dimensions, pure and covered by tests.
- `ProductCard` is now a link to the detail route, which `M1.5` deliberately left out.
- `api/client.ts` — `fetchProduct`, which separates a missing product from an unavailable service.

**Decisions taken.**

- **The `notFound()` check runs inside the `<Suspense>` boundary.** This is the shape the Next docs
  recommend for keeping the shell and loading UI while data loads. The consequence is that a
  missing slug answers `200` rather than `404`, because the response is already streaming by then —
  and Next compensates with `<meta name="robots" content="noindex">`, verified present on a missing
  product and absent on a real one. Blocking the route would buy a `404` status at the cost of the
  skeleton `UX.md` asks for; the noindex tag makes that trade the right way round.
- **The add-to-cart control is genuinely disabled, with its reason in visible text** wired via
  `aria-describedby`. Nothing is specified for a placeholder, and `US-3.1` owns the real behaviour
  at `M3`; a control that pretends to work would be worse than one that explains itself.
- **Nothing is cropped, anywhere.** `ADR-0012` excludes `BY-ND` images "from any cropping or
  alteration", the payload carries no licence for the UI to branch on, and 8 of the 46 shipped
  images are `BY-ND` — so the gallery and the card both use `object-contain`. This also corrects the
  card, which shipped with `object-cover` at `M1.5`. The source ratios are genuinely mixed, so the
  cost is letterboxing.
- **`generateMetadata` is per product**, which `US-1.2` asks for explicitly, and costs no extra
  request: Next memoises the underlying `fetch` across the metadata and the page. Verified by
  counting backend access-log lines for one page view.
- **Material, colour and dimensions are surfaced** because `UX-GOAL-1` asks for price, dimensions
  and stock to be visible before the cart. Dimensions are labelled rather than joined into
  `W × D × H`, since the three fields are independently nullable.
- **The gallery renders one image.** The source set holds one per product; multi-image galleries are
  a deferred decision, not an oversight, and the component renders from the list so more images is a
  data change.

**A bug the tests caught.** `fetchProduct` passed every case while never using the stubbed `fetch`:
`openapi-fetch` captures `globalThis.fetch` when the client is *created*, which happens at module
load, before a test can stub it. So the tests were hitting a real socket and taking the
transport-failure path, and the `503` case only appeared to pass because both paths return
`unavailable`. The client now resolves `fetch` per call, which fixes the tests and removes a real
production risk: a reference captured at import time can predate Next's replacement of `fetch`,
which is what provides the request memoisation above.

**Impact.** `/products/[slug]` builds as Partial Prerender (`◐`), like the listing. Gates green:
`typecheck`, `lint`, `format:check`, `test` (22 tests, up from 14), `build`. Verified end to end
against a real server on ports isolated from the development instance: a real product renders its
name in `<title>` and `<h1>`, its price, "In stock", description, material/colour/dimensions, the
disabled add-to-cart with its note, and a gallery image with `alt` text; exactly one API request
serves the entire view; a missing slug renders the not-found page with `noindex`; catalog cards link
to the detail route; and no server-side errors are logged.

### 2026-10-10 — v0.1.18 — M1.5 catalog listing page

**Context.** `M1.5`, the first page to read the API. Two facts discovered up front shaped it:
`cacheComponents: true` makes the app partial-prerendered by default, and `UX.md` section 5 already
asks for a loading state that this architecture provides for free.

**What changed.**

- `app/products/page.tsx` — the listing. The heading renders from the static shell; the result
  count, the grid, and the pager stream in behind one `<Suspense>` boundary.
- `components/` — `ProductCard`, `ProductGrid`, `ProductGridSkeleton`, `Pagination`, `EmptyState`,
  `RetryPanel`, `RetryButton`. `ProductGrid` exports its column classes so the skeleton reserves the
  identical shape rather than a similar one.
- `api/client.ts` — the `openapi-fetch` client, typed from `paths` in the generated schema.
- `lib/money.ts` and `lib/pagination.ts` — price formatting and page arithmetic, both pure and
  covered by tests.

**Decisions taken.**

- **One `<Suspense>` boundary, and no `loading.tsx`.** The boundary is required — with Cache
  Components an uncached fetch or a `searchParams` read outside one is a build error — and it is
  also the card-skeleton loading state the spec asks for. `loading.tsx` would have replaced the
  heading along with the grid.
- **The listing is deliberately uncached.** `use cache` would place the grid in the static shell,
  but nothing invalidates the catalog yet, so a reseed would keep serving withdrawn products until
  the lifetime expired. Caching wants an invalidation story to go with it.
- **The pager is links, not buttons.** Paging then works with no client JavaScript, and the page
  number lives in the URL — the ground `US-1.4` needs for shareable filter state.
- **A page past the end shows the empty state with the pager intact.** The API returns an empty page
  rather than a `404` precisely so the client need not special-case it; dropping the pager would
  strand a visitor who arrived on such a URL.
- **The grid's column count is a decision, because the spec does not make it.** `UX.md` section 8
  fixes the breakpoints and `ADR-0013` the tokens, but not the columns: one on the smallest screens
  for the large imagery section 1 asks for, then two, three, and four.
- **`parsePage` clamps only to a minimum of one.** A page past the end passes through on purpose,
  because that is the case the empty state exists for.
- **`ProductCard` is neither a link nor a stock indicator.** The detail route arrives at `M1.6`, so
  a link would point at a `404`; `in_stock` belongs to `US-1.2`'s acceptance criteria, not the
  listing's.
- **`PAGE_SIZE` is sent explicitly** rather than relying on the API default, so the skeleton
  reserves exactly as many cards as will arrive.

**A bug that verification caught.** Every build logged six lines of `catalog: GET /api/v1/products
did not complete … During prerendering, fetch() rejects when the prerender is complete`. The
blanket `try`/`catch` in the read client was catching React's *intentional* abort of the deferred
render under Partial Prerendering and reporting it as an unreachable backend — a false alarm that
would have sent someone hunting an outage that never happened. The fix is `unstable_rethrow(error)`
at the top of the catch, which the Next docs prescribe for exactly this case and which name `fetch`
with `cache: 'no-store'` among the APIs concerned. Build noise went from six to zero, while a
genuinely dead backend still logs and still renders the retry panel. `RUNBOOK.md` section 8 records
it.

**Impact.** `/products` builds as Partial Prerender (`◐`) — a static shell with the listing
streamed in — and serves 24 cards per page from a 46-product catalog with a working pager. Gates
green: frontend `typecheck`, `lint`, `format:check`, `test` (14 tests), `build`. Verified end to end
against a real server on ports isolated from the development instance: page one renders 24 cards
and "46 products"; page two renders 22; `?page=99` renders the empty state with a usable pager;
`?page=abc` falls back to page one; with no backend listening the retry panel renders and the page
heading survives; and starting the backend against the same build makes the grid appear with no
rebuild, confirming the read is not cached.

### 2026-10-10 — v0.1.17 — OpenAPI snapshot and generated frontend types

**Context.** `M1.4`. The frontend has to consume the `M1.3` contract without the two drifting
apart, which `API.md` section 10 already commits to. Two constraints decided the shape: `Frontend
CI` runs with no backend and is path-filtered to `frontend/**`, and a Vercel build cannot fetch a
schema from a live API.

**What changed.**

- `manage.py export_openapi_schema` writes the contract to `frontend/openapi.json`. django-ninja
  ships a command of its own, but Django only discovers management commands from applications in
  `INSTALLED_APPS`, and `ninja` is not one; its default also resolves the API instance at `/api/`,
  where this project mounts `/api/v1`. The wrapper pins both.
- `frontend/openapi.json` — the committed snapshot: 19.6 KB, four paths, fourteen schemas.
- `openapi-typescript` generates `frontend/src/api/schema.d.ts` from it via `pnpm codegen`, wired
  into `pnpm dev`, `pnpm build`, and `pnpm typecheck`. The generated file is gitignored, so a fresh
  clone needs no extra step.
- `Backend CI` regenerates the snapshot and fails on any difference, and `frontend/openapi.json` is
  now a path trigger for that workflow, so a hand-edited snapshot is caught as well.

**Decisions taken.**

- **The snapshot lives inside `frontend/`.** Vercel builds with `frontend` as its root directory, so
  `../backend/openapi.json` would not exist during a deploy. That one constraint rules out keeping
  the snapshot beside the API it describes.
- **The generated TypeScript is not committed.** The snapshot is the artifact under review; a
  committed generated file would be a copy of a copy, and `pnpm typecheck` rebuilds it anyway.
- **Formatting of the snapshot is owned by the generator, not Prettier.** `prettier --check` failed
  on it — Prettier collapses short arrays onto one line where `json.dumps` does not — so it is in
  `.prettierignore`. Without that the drift check could never pass, because the two tools disagree
  about the same bytes by construction.
- **`indent=2` and sorted keys** in the export, so a contract change shows up as the lines that
  actually changed rather than a reordered file.

**Corrected.** `RUNBOOK.md`'s `M1.3` section did not land with `v0.1.16`: that patch contained two
hunks, the second failed to anchor, and the tool discards the whole file when any hunk fails. The
section is added here, together with the `M1.4` one.

**Impact.** The contract has one source and a check that enforces it. Gates green — backend:
`ruff format --check` (39 files), `ruff check`, `basedpyright` (0 errors), `makemigrations --check`,
79 tests; frontend: `typecheck`, `lint`, `format:check`, `test`, `build`. The drift check was
verified in both directions: exit 0 on a matching snapshot, and exit 1 with the diff printed when
the snapshot is stale.

### 2026-10-10 — v0.1.16 — M1.3 catalog read API and the error envelope

**Context.** `M1.3` turns the seeded catalog into a contract the storefront can consume. It is the
first API surface, so the cross-cutting pieces land with it: the error envelope and the generated
OpenAPI schema.

**What changed.**

- `catalog/api.py` — four public routes under `/api/v1`: `GET /categories`, `GET /categories/{slug}`,
  `GET /products`, and `GET /products/{slug}`. The listing route carries pagination, filtering
  (`category`, `q`, `min_price`, `max_price`), and sorting (`name`, `price`, `-price`, `newest`).
- `catalog/schemas.py` — the response shapes. **The listing does not nest variants; the detail
  route does**, by decision: a grid never renders variants, and nesting them would multiply every
  card payload for data it does not show.
- `core/errors.py` — one error envelope, `{"error": {code, message, details, request_id}}`, per
  `API.md` section 3 (`NFR-4`). Ninja's defaults are replaced on three counts: it answers request
  validation with `422` and `{"detail": ...}` where the contract says `400` with the envelope, it
  reports a bare list rather than `{field, issue}` pairs, and in production it *re-raises* an
  unhandled exception, which produces an error body that is not JSON at all. The `request_id`
  matches the `X-Request-ID` header the middleware already sets.
- `config/api.py` — installs the error handlers and mounts the catalog router at the API root.

**Decisions taken.**

- **Filters and pagination belong to `M1.3`.** Shaping the contract once is cheaper than adding
  query parameters after `M1.4` has generated client types from it.
- **`min_price` and `max_price` are integer cents**, matching the payload convention in `API.md`
  section 1, so no client converts to a decimal in order to filter.
- **An unknown `category` filter returns zero results, not an error**; an unknown *slug* on a detail
  route is a `404`. The storefront needs a no-results state (`US-1.3`), not an error state.
- **`category` also matches descendants.** The model supports nesting even though the seed is flat,
  and a parent filter that silently dropped its children would be a latent bug.
- **`page_size` caps at 100, `page` must be at least 1, and `sort` is an enum**; anything else is a
  `400`. A page past the end is an empty page rather than a `404`, so the client renders "no more
  results" without special-casing.
- **Ordering always ends with a tiebreaker**, so a page boundary cannot shuffle between requests.
- **The listing omits `attributes`.** It holds seed bookkeeping — the curated keyword and series —
  rather than anything customer-facing.

**One `M1.1` assumption corrected.** `ADR-0014` recorded that `basedpyright` cannot see reverse
foreign keys, and suggested `prefetch_related` as part of the workaround. Writing this API showed
the limitation is wider, and the suggestion does not work: an implicit primary key (`id`) and
foreign-key attnames (`parent_id`, `product_id`) are equally invisible, because django-stubs
generates all of them in its *mypy* plugin and its own stub file states that other type checkers
will not understand them; and reading prefetched rows still needs the inaccessible accessor. So
`catalog/api.py` reads rows with `values()` and reaches related rows through
`filter(product__slug=...)`, never touching a plugin-synthesised attribute. `RUNBOOK.md` section 8
now carries both halves of the limitation.

**Impact.** The storefront has a contract: 46 products, 7 categories, and 95 variants behind four
public routes, with the OpenAPI schema at `/api/v1/openapi.json` for `M1.4` to generate types from.
Gates green: `ruff format --check` (38 files), `ruff check`, `basedpyright` (0 errors),
`makemigrations --check` (no drift), and 79 tests passing on both SQLite and PostgreSQL 17 — the
suite grew from 49. The CLI was exercised against PostgreSQL 17 as well, which confirmed the
JSON-keyword search behind `?q=` behaves identically on JSONB and on SQLite. That was the one
genuinely database-specific risk in the contract, and it is now covered by a test on both.

### 2026-10-10 — v0.1.15 — BY-ND images dropped; reverse-relation typing recorded

**Context.** Three founder decisions taken immediately after `v0.1.14`. The first reverses a
decision recorded there, and is recorded here rather than by editing that entry, because this
file is append-only.

**What changed.**

- **No `BY-ND` image ships.** `v0.1.14` shipped the bed frame, bookshelf, and dining table under
  `BY-ND-2.0`, on the grounds that `ADR-0012` permits that licence when the work is never
  altered. That reading is correct, but it hands every future layout a constraint that nothing
  checks: a grid which crops or resizes one of those files has created a derivative, and no gate
  would catch it. All three are now dropped — files removed from `frontend/public/images/`
  (49 → 46 images, 3.4 MB → 3.2 MB) and their keywords removed from the curation, so 54 of the
  100 source keywords ship rather than 51. Every vendored image is `BY`, `BY-SA`, `PDM`, or
  `CC0`, and safe to crop and resize.
- **Products fall 49 → 46 and variants 100 → 95.** "Dining Room" seeds two products now, and
  "Bedroom" and "Storage" one fewer each. `SEED` is untouched, but removing curated entries
  shifts the order that the every-tenth out-of-stock rule counts along; the number of
  out-of-stock products stays five, which the tests assert.
- **`ALLOWED_LICENCES` no longer admits `BY-ND-2.0`**, and
  `test_no_derivative_restricted_image_ships` fails if one ever reappears, so the reversal
  cannot be undone by accident.
- **`ADR-0014` records the reverse foreign-key strategy: query explicitly.** `basedpyright`
  cannot see accessors such as `product.images` — django-stubs supplies reverse relations
  through a *mypy* plugin, and pyright has no plugin mechanism — so code reaches relations
  through the manager (`ProductImage.objects.filter(product=product)`), which stays fully typed.
  Relation names as strings are allowed where the query wants them
  (`prefetch_related("images")`); casting a reverse accessor is not. The alternative was
  replacing the type checker, which `M0` had settled.
- **Single-image products stand, by decision.** The source set holds exactly one image per
  keyword, so `M1.6`'s gallery renders one image per product for now. Multi-image galleries are
  deferred deliberately, not overlooked.
- Counts in `ROADMAP.md`, `RUNBOOK.md`, and the `seed_data.py` docstring follow the new curation.

**Impact.** `manage.py seed` builds the 46-product catalogue in one command and stays safe to
re-run. Gates green: `ruff format --check` (34 files), `ruff check`, `basedpyright` (0 errors),
`makemigrations --check` (no drift — the curation change needed no migration), and 49 tests
passing on both SQLite and PostgreSQL 17. The CLI was exercised against a real PostgreSQL 17
database with the same result every time: `migrate`, `seed`, a second `seed` leaving the counts
untouched, and `seed --reset`, each ending at 7 / 46 / 95 / 46 / 46.

### 2026-10-10 — v0.1.14 — M1.2 catalog seed landed

**Context.** `M1.2` turns the `M1.1` schema into a browsable catalog and settles the
`some_source/` question: the reference image set lives outside the repository, while `ADR-0012`
requires `manifest.csv` to be kept inside it.

**What changed.**

- **The image set is vendored into the repository.** 49 curated images move to
  `frontend/public/images/` (3.4 MB), and `manifest.csv` is copied byte-for-byte to
  `backend/seed_data/manifest.csv`. `ADR-0012`'s provenance requirement now holds, and the seed
  can run in CI and on the deployed demo instead of only on the founder's machine.
- `catalog/seed_data.py` — curation as data: which of the 100 source keywords ship, into which of
  7 categories, plus the series/material/finish, price-band, and dimension vocabulary. The source
  set covers a whole house, so appliances, cleaning tools, and kitchenware are excluded by
  omission; 51 keywords never ship.
- `catalog/seeders.py` — 7 categories, 49 products, 100 variants, 49 images, 49 credits.
- `catalog/migrations/0002` and `0003` — uniqueness on `ImageCredit.source_page_url` and
  `(ProductImage.product, path)` so upserts are idempotent, plus `ImageCredit.title` widened to 300.
- `core/seeding.py` — rewritten as declarative discovery. `M0.8` registered steps as an import
  side effect, which is unsound: Python caches modules, so after any registry reset the step
  vanished silently and `manage.py seed` would do nothing without erroring.
- `tests/test_catalog_seed.py` added; `tests/test_seed.py` now injects steps per test instead of
  mutating global state.

**Decisions taken.**

- **Curation is data, not code.** One mapping drives the seed, the vendored images, and `M1.9`'s
  credits page, so they cannot disagree. `seed()` fails loudly when a curated keyword is absent
  from the manifest.
- **`random.Random(SEED)`, not Faker.** `DATA-MODEL.md` §7 says "a deterministic Faker seed".
  Faker is not used: its prose is generic, and `UX.md` §9 asks for plain, warm copy. Determinism —
  the actual requirement — comes from a seeded generator plus curated copy templates.
  `seeders.SEED` changes the whole catalog.
- **Out-of-stock is deliberate.** Every tenth curated product is seeded with no stock, so the
  storefront always has that state to render. Left to `randint(0, 40)` it never occurred at all.
- **Three `BY-ND` images ship unaltered.** `ADR-0012` permits `BY-ND` only if never modified, and
  dropping them would strip the dining table, bookshelf, and bed frame. They are copied verbatim
  and must never be cropped or re-rendered; a test pins the exact set.
- **Images are served by Next.js, not Django.** `ProductImage.path` holds a root-relative URL
  (`/images/armchair.webp`) — cheaper than streaming files through the API, and it matches the
  Vercel deployment.
- **`--reset` clears the whole catalog**, because nothing yet distinguishes seeded rows from
  operator-created ones. That becomes a real hazard at `M5`.

**Two problems PostgreSQL found that SQLite could not see.**

1. `alt` text overflowed `varchar(200)`. It concatenated the product name with the photo's source
   title, and those titles run to 255 characters — while the median is 24.5, so the silent SQLite
   run looked like success. `ImageCredit.title` had the same latent overflow and was widened.
2. The missing out-of-stock state above: a case the UI needs that the generator happened not to
   produce.

Both are now guarded by `full_clean()` over every seeded row, since SQLite does not enforce
`max_length`.

**Impact.** `manage.py seed` builds the catalog in one command and is safe to re-run. Gates green:
`ruff format --check` (34 files), `ruff check`, `basedpyright` (0 errors), `makemigrations --check`
(no drift), and 49 tests passing on both SQLite and PostgreSQL 17. The CLI was also exercised
against a real PostgreSQL 17 database: `migrate`, `seed`, a second `seed` with identical row
counts, and `seed --reset`, ending at 7 / 49 / 100 / 49 / 49.

**A tooling note worth recording.** The `M1.1` RUNBOOK section that `apply_patch` reported as
applied in `v0.1.12` was never written to disk. It was found missing during this increment,
confirmed absent from the `9389b73` commit, and is now added together with the `M1.2` section.
Every other document change from that patch did land. Document edits now get read back rather than
trusted.

### 2026-10-10 — v0.1.13 — M0 complete, CI confirmed green

**Context.** `M0` could not be closed while its second exit criterion was unverifiable. The
founder pushed `9389b73`, which closed the loop and confirmed the `v0.1.11` CI fix.

**What was confirmed.**

- **`Backend CI` run #2 on `9389b73` — success, 42s.** This is the first time the backend job has
  ever actually executed: run #1 died at "Set up job" on the bad `setup-uv` pin. The job now
  genuinely runs `ruff format --check`, `ruff check`, `basedpyright`, and `pytest` against a
  PostgreSQL 17 service.
- **`Frontend CI` — success on `7b06e88`.** It did not re-run for `9389b73`, because the workflow
  is path-filtered to `frontend/**` and nothing under `frontend/` changed between the two
  commits, so that green still describes the current tree.
- **`docker compose up` runs API + web** — verified during `M0.7`.

Both exit criteria now hold, so `M0` is marked `[x]` in `ROADMAP.md`.

**Impact.** All ten `M0` increments are complete and the delivery pipeline is green for the first
time. The lesson from `v0.1.11` is why this entry exists: a workflow that has never run is not
evidence of anything, and only a push can establish that it has. `RUNBOOK.md` §6 now carries that
caveat, including the path-filter subtlety above.

### 2026-10-10 — v0.1.12 — M1.1 catalog models landed

**Context.** M1 begins: the catalog gets its physical schema, so `M1.2` can seed it and `M1.3`
can serve it.

**What was added.**

- A `catalog` app with `Category`, `Product`, `ProductVariant`, `ProductImage`, and
  `ImageCredit`, following `DATA-MODEL.md` §2. Money is integer cents throughout;
  `Product.attributes` is JSONB for specs that do not warrant a column.
- `core/models.py` — `TimeStampedModel`, the abstract base giving every table
  `created_at` / `updated_at` as `DATA-MODEL.md` §2 requires.
- `catalog/migrations/0001_initial.py` — generated, reviewed, unmodified.
- `tests/test_catalog_models.py` — 13 tests: `__str__` labels, unique slugs and SKUs, category
  nesting, `PROTECT` on `Product.category`, cascades to variants and images, `SET_NULL` on an
  image's credit, orderings, and rejection of negative money and stock.

**Decisions taken.**

- **`Product.category` is `PROTECT`; `ProductImage.credit` is `SET_NULL`.** `DATA-MODEL.md`
  lists both as foreign keys without an `on_delete`. Deleting a category must not silently take
  its products with it, and deleting a credit must not delete the image that uses it.
- **Each concrete `Meta` subclasses `TimeStampedModel.Meta`.** Two reasons: Django sets
  `abstract=False` on a base `Meta` before installing it, so a subclassing child stays concrete
  (verified — all five report `_meta.abstract is False`), and basedpyright would otherwise
  raise `reportIncompatibleVariableOverride` on every `Meta`.
- **All five models declare `Meta.ordering`.** Deterministic defaults keep pagination stable
  once `M1.5` and `M1.7` add paging and sorting over these tables.
- **`basedpyright` now covers `catalog`.** Its `include` list named only `config`, `core`, and
  `tests`, so the new app would otherwise have escaped type checking entirely.
- **`ImageCredit` maps the manifest by column:** `source_title → title`, `creator → creator`,
  `license → license`, `source → source`, `source_page → source_page_url`. The names differ
  between the manifest and `DATA-MODEL.md`; `M1.2` owns the import.

**Impact.** The catalog schema exists, migrates cleanly, and matches the models exactly. Backend
gates green: `ruff format --check` (31 files), `ruff check`, `basedpyright` (0 errors),
`makemigrations --check` (no drift), and `pytest` — 30 passed on SQLite and 30 passed against
PostgreSQL 17.

One limitation is now recorded in `RUNBOOK.md` §8 rather than hidden: **basedpyright cannot see
reverse foreign-key accessors**, so `category.children` and `product.images` are untyped. The
tests query explicitly instead. This needs a decision — and an ADR — before `M1.3`.

### 2026-10-10 — v0.1.11 — Backend CI unblocked (setup-uv pin corrected)

**Context.** The first push of the `M0.9` workflows revealed that `Backend CI` had been failing
since the moment it was created. Only a push could surface this: the assistant commits locally
and cannot run GitHub Actions.

**What happened.** The run died at "Set up job" with
`Unable to resolve action 'astral-sh/setup-uv@v8', unable to find version 'v8'`, before a single
gate executed. The pin came from a web search that reported `v8.3.2`. Setup-uv does publish full
versions from `v8.3.2` through `v10.3.0`, but it **stopped publishing floating major tags after
`v7`**, so `v8`, `v9`, and `v10` do not exist.

**What changed.**

- `backend.yml` pins `astral-sh/setup-uv@v10.3.0`, confirmed against the repository's tag list
  *and* its `action.yml` rather than a search result.
- CI pins uv to `0.12.5`, matching `backend/Dockerfile`. It would otherwise have installed the
  latest uv while the container ran `0.12.5` — silent drift between the two paths.
- The failure mode is recorded in `RUNBOOK.md` §8 so the next person checks the tag list first.

**Impact.** `Frontend CI` passed on the same push, which retroactively confirms `checkout@v6`,
`pnpm/action-setup@v4`, and `setup-node@v7` all resolve. **The corrected pin is still unverified
until the next push** — this entry records a fix, not a green run. `M0` therefore stays `[~]`;
it closes when a push shows `Backend CI` green.

### 2026-10-10 — v0.1.10 — Tailwind CSS adopted (revises M0.2)

**Context.** The founder reversed the `M0.2` "no styling framework" decision before the catalog
UI is built, so the storefront is written in one styling system instead of two. Recorded as
`ADR-0013` — the ADR the `v0.1.6` entry asked for.

**What changed.**

- `ADR-0013-tailwind-css.md` — the decision, the options considered, and the consequences; added
  to the decision index in `ARCHITECTURE.md` §11.
- `tailwindcss` and `@tailwindcss/postcss` 4.3.3, plus `postcss` 8.5.29, as frontend
  devDependencies, wired through a new `postcss.config.mjs`.
- `src/app/globals.css` — rewritten around `@import "tailwindcss"` and a `@theme` block that
  declares the `UX.md` §2 tokens, so Tailwind generates utilities from them. A small
  `@layer base` keeps the rules that must hold on every route: the `:focus-visible` ring
  (`UX.md` §7), heading line-height and `text-wrap: balance`, the anchor colour, and the body
  background and text colours.
- `src/app/page.tsx` — the placeholder composes utilities now, and `src/app/page.module.css` is
  deleted, retiring CSS Modules.
- `frontend/README.md` — the styling convention points at Tailwind and the `@theme` block.

**Decisions taken.**

- **Token *declaration* moves; token *values* do not.** `UX.md` §2 stays the source of truth —
  the values are declared in `@theme` instead of as standalone custom properties. No colour,
  size, or measure changed.
- **Custom theme entries only where Tailwind's defaults differ.** The project's 4px spacing scale
  and its 8px/16px radii are exactly Tailwind's defaults, so no `--spacing-*` or `--radius-*`
  entries were added: `p-4` and `rounded-lg` already mean the token values. Only the palette, the
  type scale, the 70ch measure, and the font stack needed declaring.
- **A `@layer base` for cross-cutting rules.** The focus ring is an accessibility requirement on
  every route (`UX.md` §7), so it stays global rather than being repeated per component and
  eventually forgotten.
- **The `v0.1.6` entry is not rewritten.** It was accurate when written; this entry and
  `ADR-0013` record the reversal, per the append-only rule.

**Impact.** The frontend styles through one system, and `M1.5`–`M1.9` are written in it from
their first commit. Frontend gates green: `typecheck`, `lint`, `format:check`, `vitest`
(2 passed), and `build`. The build is the meaningful check — Tailwind only fails loudly when
PostCSS compiles the CSS — and the emitted stylesheet was inspected directly: 7.6 KB containing
the palette (`#faf7f2`), the `70ch` measure, and the generated `max-w-measure`, `text-muted`,
and `tracking-tight` utilities, with the `focus-visible` and `text-wrap` base rules intact.

### 2026-10-10 — v0.1.9 — M0.8 seed command skeleton landed

**Context.** The last M0 increment: a seeding entry point that later milestones fill in, so the
command's contract is fixed before there is any data to seed.

**What was added.**

- `core/seeding.py` — a registry of `SeedStep` entries. A step carries a `name`, an idempotent
  `run` callable, and an optional `clear` hook used by `--reset`.
- `core/management/commands/seed.py` — `manage.py seed`. Runs every registered step in
  registration order inside a single transaction; `--reset` calls each `clear` hook first, in
  reverse registration order.
- `tests/test_seed.py` — nine tests covering ordering, the `--reset` hook, steps with no
  `clear`, the empty-registry path, fail-fast, and the registry's snapshot semantics.

**Decisions taken.**

- **A registry, not hard-coded seeding.** With no models until `M1.1`, the only way to make the
  two properties the roadmap asks for — *idempotent* and `--reset` — real and testable is for
  the command to execute something. The registry is that seam: `M1.2` registers the catalog
  seeders without touching the command.
- **One transaction for the whole run.** A failure part-way through leaves neither a
  half-seeded database nor, under `--reset`, a wiped-but-unfilled one. The run aborts instead of
  reporting success, which `test_a_failing_step_aborts_the_run` pins.
- **`clear` hooks run in reverse registration order**, so rows are deleted before the rows they
  depend on.
- **Idempotency is a contract on each step, not something the command can enforce.** The
  skeleton proves the command's mechanics; every real seeder is responsible for its own
  re-runnability, and `M1.2` must cover that with its own tests.

**Impact.** Every M0 increment has landed, and `uv run python manage.py seed` runs with and
without `--reset`. Backend gates green — `ruff format --check` (26 files), `ruff check`,
`basedpyright` (0 errors), `pytest` (17 passed, up from 8).

The M0 milestone row stays `[~]` rather than `[x]`: its exit criteria include "CI passes", and
the `M0.9` workflows have not yet run on GitHub, because pushing is the founder's call
(`WORKING-AGREEMENT.md` §1.4). M0 closes once the first push goes green.

### 2026-10-10 — v0.1.8 — M0.9 continuous integration landed

**Context.** With the compose stack proven, M0.9 wired the quality gates into GitHub Actions so
a push or a pull request is checked without anyone running the commands by hand.

**What was added.**

- `.github/workflows/backend.yml` — `ruff format --check`, `ruff check`, `basedpyright`, and
  `pytest`, on Python provisioned by `uv` from the lockfile.
- `.github/workflows/frontend.yml` — `pnpm typecheck`, `lint`, `format:check`, `test`, and
  `build`, on Node 24 with the pnpm store cached.
- Both are path-filtered (`backend/**` and `frontend/**`), so a change to one app does not run
  the other's gates; each also re-runs when its own workflow file changes.

**Decisions taken.**

- **Native path filters across two workflows.** The roadmap asks for "path-filtered jobs".
  Job-level filtering inside a single workflow needs a third-party action such as
  `dorny/paths-filter`; two workflows using `on.push.paths` / `on.pull_request.paths` reach the
  same result with no extra dependency. The trade-off is that a docs-only change reports no
  checks at all instead of a green skip. Acceptable while `main` is unprotected.
- **The backend job runs a real PostgreSQL service.** Settings fall back to SQLite only when
  `DATABASE_URL` is empty, so leaving it unset would have tested an engine the project never
  deploys on. The job provisions PostgreSQL 17 — the same version as `compose.yml`.
- **Actions are pinned to major tags** (`checkout@v6`, `setup-uv@v8`, `pnpm/action-setup@v4`,
  `setup-node@v7`) rather than commit SHAs. Major tags are the ecosystem norm and stay readable;
  SHA pinning is the stronger supply-chain posture and is worth revisiting before the project
  faces real customers.
- `pnpm` is pinned to `12.3.4` in the workflow to match `packageManager` in
  `frontend/package.json`; the two must move together.
- Concurrency groups cancel a superseded run on the same ref, so a quick second push does not
  queue behind the first.

**Impact.** The CI configuration is complete and was validated locally with `actionlint`, and
the backend suite was re-run against PostgreSQL 17 before the commit. The workflows have
**not** executed on GitHub — the working agreement has the assistant commit locally and the
founder decide when code reaches GitHub — so the M0 exit criterion "CI passes" stays unverified
until the first push. M0 is down to `M0.8` (seed command).

### 2026-10-10 — v0.1.7 — M0.7 compose stack landed

**Context.** Both apps booted on the host; M0.7 made the whole system start with one command so
a reviewer can run the demo without installing Python, Node, or Postgres.

**What was added.**

- `compose.yml` — Postgres 17, the API, and the web app, with health-gated start ordering and a
  named `db-data` volume. Every connection value comes from the environment with a local
  default, so `docker compose up --build` needs no `.env` file.
- `backend/Dockerfile` — `python:3.13-slim` with `uv`; dependencies install from the lockfile
  into `/opt/venv` in a cached layer, then the source is copied. Runs Uvicorn on the ASGI app.
- `frontend/Dockerfile` — multi-stage Node 24 with `pnpm`; dependencies install from the
  lockfile, `pnpm build` runs in the builder, and the runner starts the built app.
- `backend/.dockerignore`, `frontend/.dockerignore` — keep host artefacts (`.venv`,
  `node_modules`, `.next`, `db.sqlite3`) and the local `.env` out of the build context.

**Decisions taken.**

- The API container runs `manage.py migrate --noinput` before Uvicorn. Migrations are
  idempotent, so a fresh volume needs no manual step and a restart is harmless.
- The Postgres port is **not** published to the host by default. Only database clients need it,
  and leaving it closed avoids a collision on a machine that already runs Postgres; the entry
  ships commented in `compose.yml`.
- The web image runs the **production** build (`pnpm build` → `pnpm start`) rather than
  `pnpm dev`, so the container exercises the artefact that actually ships. A Next.js
  `standalone` output would shrink the image further, but it interacts badly with `pnpm`'s
  symlinked `node_modules`; that optimisation is deferred until image size matters.
- No source bind-mounts. Compose is the "does the whole system work together" path; the fast
  edit loop stays on the host (`uv run uvicorn --reload`, `pnpm dev`), as the runbook documents.

**Impact.** `docker compose up --build` brings up all three services from a clean checkout.
Remaining M0 items: `M0.9` CI, then `M0.8` seed command.

### 2026-10-09 — v0.1.6 — M0 frontend skeleton landed

**Context.** With the backend skeleton committed, M0 continued with the Next.js application so
both apps boot and the quality gates cover both sides.

**What was added.**

- `frontend/` — Next.js 16.4 (App Router, RSC, Turbopack) with TypeScript `strict`, managed by
  `pnpm`.
- The design tokens from `UX.md` §2 are now the single source of truth in
  `src/app/globals.css` (the `--lys-*` custom properties), with a minimal base layer: warm
  canvas, ink text, a visible `:focus-visible` ring, and image defaults.
- `src/app/layout.tsx` — `lang="en"`, Inter through `next/font`, LYSHEIM metadata.
- `src/app/page.tsx` — a minimal branded placeholder (one `<h1>`, one `<main>` landmark).
- Tooling: ESLint 9 flat config (`core-web-vitals` + `typescript` + `eslint-config-prettier`),
  Prettier, `vitest`, and a root `.editorconfig`.
- Gate scripts: `typecheck`, `lint`, `format:check`, `test`, `build`.
- `src/lib/config.ts` — `getApiBaseUrl()` reads `NEXT_PUBLIC_API_BASE_URL` with a localhost
  fallback, covered by two tests.
- `frontend/.env.example` documenting `NEXT_PUBLIC_API_BASE_URL`.

**Decisions taken.**

- **No styling framework.** The docs specify design tokens in `globals.css` and never mention
  Tailwind, so the scaffold uses plain CSS with `--lys-*` tokens plus CSS Modules. Adopting a
  CSS framework is deferred to its own ADR before the catalog UI is built at `M1.5`.
- `typecheck` runs `next typegen && tsc --noEmit` — Next 16 generates `LayoutProps` and the
  route types, so a bare `tsc --noEmit` fails on a fresh checkout.
- The vitest config uses the `.mts` extension so Vite loads it as ESM.
- `@types/node` raised to `^24` to match the Node runtime and satisfy `vitest@5`'s peer range.

**Impact.** Both applications boot. Backend gates unchanged and green. Frontend gates green:
`lint`, `format:check`, `vitest` (2 passed), `typecheck`, `build` (4 static pages). Boot smoke
test: `GET /` returns 200 and renders `LYSHEIM`. Remaining M0 items: `M0.7` compose, `M0.8`
seed command, `M0.9` CI.

### 2026-10-09 — v0.1.5 — M0 backend skeleton landed

**Context.** Planning closed at v0.1.4. M0 (foundations) began with the backend skeleton —
the Django 6 + Django Ninja service every later increment builds on.

**What was added.**

- `backend/` — a `uv`-managed project: `config/` (settings split `base`/`dev`/`prod`, URL
  config, Ninja API instance, ASGI and WSGI entrypoints), `core/` (request-ID middleware,
  health view, JSON log formatter), `manage.py`, `pyproject.toml`, `uv.lock`, `.env.example`,
  `README.md`.
- `GET /healthz` returns `{"status": "ok", "request_id": ...}` and always sets an
  `X-Request-ID` response header, echoing a caller-supplied value when present.
- API surface under `/api/v1`: `GET /api/v1/openapi.json` and `GET /api/v1/docs`.
- `tests/` — four pytest tests covering the health contract and the OpenAPI schema.
- Configuration is environment-only (`django-environ`), with a SQLite fallback so a bare
  checkout and the test suite run without infrastructure; PostgreSQL is used via
  `DATABASE_URL`.

**Decisions taken.**

- `uvicorn[standard]` added as a runtime dependency — it serves both local runs and the
  Render deploy, and `uv run uvicorn config.asgi:application` is the documented run command.

**Impact.** First application code in the fresh-start repository. All gates green:
`ruff format --check` (19 files), `ruff check`, `basedpyright` (0 errors), `pytest` (4
passed). ASGI smoke test: `/healthz` → `200`, `/api/v1/openapi.json` → `200`. `PLAN.md` is
unchanged at v0.1.4.

### 2026-10-09 — v0.1.4 — Quality standards baselined (planning phase complete)

**Context.** Stage 5 (cross-cutting) produced the security, review, and collaboration
standards, closing the planning phase.

**What was added.**

- `06-quality/SECURITY-BASELINE.md` — scope and data classification, trust boundaries, a
  STRIDE threat model, twelve findings (`SEC-FIND-1.1..12`) with risk and remediation, a
  secure-configuration baseline, detection/incident-response, and privacy handling.
- `06-quality/CODE-REVIEW-STANDARD.md` — the review ritual, severity levels, and the checklist
  that must pass before any commit.
- `06-quality/AGENT-TOPOLOGY.md` — the founder/assistant/tester-agent topology, handoff
  contracts, communication protocol, memory model, failure recovery, and evaluation signals.
- `_working/TODO_cybersecurity.md`, `TODO_code-reviewer.md`, `TODO_multi-agent-orchestrator.md`.

**Impact.** `PLAN.md` re-baselined to v0.1.4. **The planning phase (Stages 0–5) is complete.**
No application code written yet; the next step is M0 (foundations).

### 2026-10-09 — v0.1.3 — Delivery plan baselined

**Context.** Stage 4 (delivery) turned the workstreams into a sequenced, incremented roadmap
and formalised delivery governance.

**What was added.**

- `04-delivery/ROADMAP.md` — milestones `M0`–`M8` with concrete increments, sequencing and
  dependencies, RACI, Definition of Done, and change control.
- `04-delivery/RISK-REGISTER.md` — the full register `RISK-1..9`, reviewed at every milestone
  gate.
- `04-delivery/RUNBOOK.md` — the runbook skeleton, filled in one entry per increment.
- `_working/TODO_technical-lead.md` — raw technical-lead file; `_working/TODO_technical-project-manager.md`
  extended with the Stage 4 items.

**Impact.** `PLAN.md` re-baselined to v0.1.3. No application code written yet.

### 2026-10-09 — v0.1.2 — Architecture baselined

**Context.** Stage 3 (architecture) produced the system, domain, and API designs and closed
the three product decisions deferred from Stage 2.

**What was added.**

- `03-architecture/ARCHITECTURE.md` — C4 context, container, and component views; bounded
  contexts; integration flow; NFR architecture; deployment topology; a Phase 2 data-platform
  outline.
- `03-architecture/DATA-MODEL.md` — ERD, tables, enumerations, indexes, money handling,
  migration and seeding strategy.
- `03-architecture/API.md` — REST contract, conventions, error envelope, and endpoints.
- `decisions/ADR-0005..0012` — API style, async & tasks, operator console, cart & guest
  merge, auth & tokens, mock-first payments, deployment stack, and image licensing.
- `_working/TODO_*` — raw system-architect, backend, frontend, data-engineer, and
  cloud-engineer files.

**Decisions closed.** `D1` → Django admin as the v1 operator console (`ADR-0007`). `D2` →
server-side cart with a guest cookie merged on login (`ADR-0008`). `D3` → in-memory access
token plus an httpOnly refresh cookie (`ADR-0009`).

**Impact.** `PLAN.md` re-baselined to v0.1.2. No application code written yet.

### 2026-10-09 — v0.1.1 — Product scope baselined

**Context.** Stage 2 (product) produced the curated scope and UX documents.

**What was added.**

- `02-product/SCOPE.md` — personas, epics `EPIC-1..7`, user stories with acceptance
  criteria, in/out of scope, NFRs `NFR-1..9`, and the v1 Definition of Done. Three open
  decisions (`D1` operator-console form, `D2` guest cart, `D3` token storage) are deferred to
  Stage 3.
- `02-product/UX.md` — visual language and design tokens, information architecture, key
  flows, states matrix, component inventory, accessibility and responsive requirements, and
  the validation plan.
- `_working/TODO_technical-project-manager.md`, `_working/TODO_ui-ux.md` — raw agent files.

**Impact.** No change to the plan itself; product detail elaborated. `PLAN.md` re-baselined
to v0.1.1. No application code written yet.

### 2026-10-09 — v0.1.0 — Project reset and re-baseline

**Context.** The repository previously contained a complete earlier iteration of this
project (brand `NORDVIK`) that was erased in commits `1bb7969` ("erase content") and
`64550f3` ("erase all"). The founder chose a **fresh start**: re-plan the project from zero
rather than resume the prior code, reusing the prior *documentation conventions* because
they were sound.

**Decisions taken in this baseline.**

- Fresh start; prior work treated as discarded (recoverable at `d23c8de` if ever needed).
- Brand **LYSHEIM** adopted (`ADR-0003`).
- Monorepo structure with `backend/`, `frontend/`, `docs/` (`ADR-0001`).
- Documentation and change-control convention reused (`ADR-0002`).
- Working agreement adopted: small increments, quality gates, unit tests, local commit
  without push, scenario-based QA, seeding, environment segregation (`ADR-0004`, see
  `WORKING-AGREEMENT.md`).
- Market changed to **international, USD** (the prior iteration targeted Indonesia/IDR).
- Stack updated to **Django 6** with an explicit async + built-in Tasks policy (see
  `PLAN.md` §5).
- Free-tier deploy targets fixed: Render (backend), Vercel (frontend), Supabase (Postgres),
  Upstash (Phase 2).

**Impact.** `PLAN.md` baselined at v0.1.0. Stage 0 (foundation) and Stage 1 (business
strategy) documentation produced. No application code written yet.
