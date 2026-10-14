# Runbook — LYSHEIM

> Owner: Founder. This runbook grows one entry per increment (see
> [`../WORKING-AGREEMENT.md`](../WORKING-AGREEMENT.md) §1.6). It will be filled in as the code
> lands; the structure below is fixed now so every increment has somewhere to document itself.

---

## 1. Prerequisites

- Python 3.12+ and [`uv`](https://docs.astral.sh/uv/)
- Node.js 20+ and [`pnpm`](https://pnpm.io/)
- Docker (for PostgreSQL and Compose)

## 2. Local development

> Filled in at M0; extended at M2.2 with the host-only database recipe.

The whole stack:

```
# (M0) compose up — API + web + Postgres
docker compose up
```

Just the database, with the API and the test suite run from the host. This is the setup the `M2.2`
verification used, and on it the backend runs on the same engine as production rather than falling
back to SQLite:

```bash
docker compose up -d db                 # PostgreSQL 17 on localhost:5432
cp backend/.env.example backend/.env    # DATABASE_URL is already the right value for the container
cd backend
uv run python manage.py migrate
uv run python manage.py seed --reset    # 7 categories, 46 products
uv run uvicorn config.asgi:application --reload
```

To go back to SQLite, comment out `DATABASE_URL` in `backend/.env`. Nothing else changes: every
command in this runbook works either way, which is what `ADR-0011`'s configuration-over-code rule is
for.

## 3. Backend

```
# (M0) install
uv sync
# (M0) run
uv run uvicorn config.asgi:application --reload
# (M0) quality gates
uv run ruff check . && uv run ruff format --check . && uv run basedpyright
# (M0) tests; `--cov` adds `NFR-7`'s coverage gate (M6.1) — the threshold and the measured scope
# live in `backend/pyproject.toml`, so this and CI enforce the same number from the same place
uv run pytest --cov
# (M0) migrate
uv run python manage.py migrate
# (M1) seed demo data (idempotent; --reset clears first)
uv run python manage.py seed --reset
```

## 4. Frontend

```
# (M0) install
pnpm install
# (M0) run (http://localhost:3000)
pnpm dev
# (M0) quality gates
pnpm typecheck && pnpm lint && pnpm test && pnpm build
```

## 5. Health check

```
curl -fsS http://localhost:8000/healthz
```

## 6. Verification per increment

Each increment's commit message and the assistant's report state exactly what to run. This
section accumulates one short entry per increment as they land.

### M0 — backend skeleton

Run it:

```bash
cd backend
uv sync
cp .env.example .env        # optional — without it, dev settings + SQLite are used
uv run python manage.py migrate
uv run uvicorn config.asgi:application --port 8000
```

Verify it:

```bash
# 200 with {"status": "ok", "request_id": "..."} and an X-Request-ID response header
curl -i http://localhost:8000/healthz

# 200 — the generated OpenAPI schema (human-readable UI at /api/v1/docs)
curl -o /dev/null -w '%{http_code}\n' http://localhost:8000/api/v1/openapi.json

# gates — 4 passed
uv run ruff format --check . && uv run ruff check . && uv run basedpyright && uv run pytest
```

Note: `/healthz` echoes a caller-supplied `X-Request-ID`; supply your own to trace a request
across the JSON logs.

### M0 — frontend skeleton

Run it:

```bash
cd frontend
pnpm install
cp .env.example .env.local
pnpm dev
```

Verify it:

```bash
# 200, rendering the LYSHEIM placeholder; the API is expected on :8000
curl -s http://localhost:3000 | grep -o 'LYSHEIM'

# gates — all must pass
pnpm typecheck && pnpm lint && pnpm format:check && pnpm test && pnpm build
```

Note: `pnpm typecheck` runs `next typegen` first. Next 16 generates the route and layout types
that `tsc` needs, so typecheck fails on a fresh checkout without that step.

### M0 — compose stack (M0.7)

Run it:

```bash
# from the repository root
docker compose up --build
```

Verify it:

```bash
# 200 with {"status": "ok", ...}
curl -fsS http://localhost:8000/healthz

# 200, rendering the LYSHEIM placeholder
curl -fsS http://localhost:3000 | grep -o LYSHEIM

# three services up; db and api report healthy
docker compose ps
```

Note: the API waits for Postgres to report healthy before it migrates, and the web container
waits on the API health endpoint, so a cold `up` finishes a few seconds after the last image
builds. Re-run with `--build` after changing a manifest or lockfile; otherwise layers are cached.

### M0 — continuous integration (M0.9)

Run it — the founder pushes; the assistant only ever commits locally (see
[`../WORKING-AGREEMENT.md`](../WORKING-AGREEMENT.md) §1.4):

```bash
git push origin main          # or open a pull request
```

The workflows are path-filtered: the backend job runs only for `backend/**` and the frontend
job only for `frontend/**`. A docs-only change runs neither.

As of `v0.1.13` both workflows are green on `main`. Note that a backend-only commit will not
re-run `Frontend CI` — check the workflow's last run against the current tree, not the latest
commit, before calling the frontend green.

Verify it:

```bash
# the gates CI runs, backend
cd backend && uv run ruff format --check . && uv run ruff check . && uv run basedpyright && uv run pytest

# the gates CI runs, frontend
cd frontend && pnpm typecheck && pnpm lint && pnpm format:check && pnpm test && pnpm build

# validate the workflow files themselves, without pushing
docker run --rm -v "$(pwd):/repo" -w /repo rhysd/actionlint:latest -color .github/workflows/*.yml
```

Note: the backend job provisions PostgreSQL 17 and sets `DATABASE_URL`, so the suite runs on the
same engine as `compose.yml` instead of the SQLite fallback. To reproduce that locally:

```bash
docker run -d --name lysheim-pg -e POSTGRES_USER=lysheim -e POSTGRES_PASSWORD=lysheim -e POSTGRES_DB=lysheim -p 55432:5432 postgres:17-alpine
cd backend && DATABASE_URL=postgres://lysheim:lysheim@localhost:55432/lysheim uv run pytest
docker rm -f lysheim-pg
```

### M0 — seed command (M0.8)

Run it:

```bash
cd backend
uv run python manage.py seed            # idempotent; safe to re-run
uv run python manage.py seed --reset    # clears seeded rows first
```

Verify it:

```bash
# prints "No seeders registered yet: nothing to seed or reset." until M1.2 registers the catalog
uv run python manage.py seed

# the flag is documented
uv run python manage.py seed --help

# the command's contract is covered by tests
uv run pytest tests/test_seed.py -q
```

Note: the seeders themselves arrive with the catalog at `M1.2`. They are registered in
`core/seeding.py`, run in registration order inside a single transaction, and each must be
idempotent — that is what makes a bare `manage.py seed` safe to re-run. `--reset` calls the
optional `clear` hook of each step in reverse order before seeding.

### M0 — Tailwind styling (M0.2, revised)

Run it:

```bash
cd frontend
pnpm install
pnpm dev
```

Verify it:

```bash
# gates — Tailwind runs inside the Next build, so a broken @theme fails the build
pnpm typecheck && pnpm lint && pnpm format:check && pnpm test && pnpm build

# 200, rendering the LYSHEIM placeholder
curl -s http://localhost:3000 | grep -o 'LYSHEIM'
```

Note: styling is Tailwind CSS (`ADR-0013`). The design tokens from `UX.md` §2 are declared in
the `@theme` block in `frontend/src/app/globals.css`, so `bg-canvas`, `text-ink`, and
`max-w-measure` are generated from those values. Changing a token means editing that block, not
adding a custom class. CSS Modules are retired.

### M1 — catalog models (M1.1)

Run it:

```bash
cd backend
uv run python manage.py migrate
```

Verify it:

```bash
# no drift between the models and catalog/migrations/0001_initial.py
uv run python manage.py makemigrations --check --dry-run

# every catalog model is concrete (not abstract)
uv run python -c "import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings.dev'); django.setup(); from catalog import models; print([(m.__name__, m._meta.abstract) for m in (models.Category, models.Product, models.ProductVariant, models.ProductImage, models.ImageCredit)])"
```

Note: `TimeStampedModel` in `core/models.py` is abstract and has no table of its own. Each
concrete model's `Meta` **subclasses** `TimeStampedModel.Meta`. Two reasons: Django sets
`abstract=False` on a base `Meta` before installing it, so a subclassing child stays concrete,
and basedpyright otherwise reports `reportIncompatibleVariableOverride` on every `Meta`.

### M1 — catalog seed (M1.2)

Run it:

```bash
cd backend
uv run python manage.py migrate
uv run python manage.py seed           # idempotent, safe to re-run without --reset
uv run python manage.py seed --reset   # clears the catalog first
```

Verify it:

```bash
uv run pytest tests/test_catalog_seed.py -q

# 7 46 95 46 46 — categories, products, variants, images, credits
uv run python -c "import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings.dev'); django.setup(); from catalog.models import Category, Product, ProductVariant, ProductImage, ImageCredit; print(Category.objects.count(), Product.objects.count(), ProductVariant.objects.count(), ProductImage.objects.count(), ImageCredit.objects.count())"
```

Notes:

- The catalog derives from two files: `catalog/seed_data.py` (which keywords are curated, into
  which category, plus the name, price, and dimension vocabulary) and
  `backend/seed_data/manifest.csv` (provenance for every credit). Change either and the catalog
  changes. Change `seeders.SEED` and every generated name, price, dimension, and stock level
  changes.
- Images live in `frontend/public/images/` and are served by Next.js, not Django.
  `ProductImage.path` is the root-relative URL the client requests.
- `--reset` clears the **whole** catalog, not just seeded rows, because nothing distinguishes a
  seeded product from an operator-created one. At `M5` that becomes a way to delete real work.
- **No `BY-ND` image ships.** `ADR-0012` prefers `BY`, `BY-SA`, and `PDM`, and `BY-ND` forbids
  derivatives — something a product grid cannot promise never to create. The three `BY-ND`
  keywords in the source set (bed frame, bookshelf, dining table) are therefore excluded with
  everything else that does not fit, and every vendored image is safe to crop and resize.
  `tests/test_catalog_seed.py` fails if a licence outside the allowed set ever appears.
- **"Dining Room" ships without a dining table, on purpose.** The only table in the source set is
  `BY-ND`. The two-product category was accepted for v1 rather than merging it into Living Room or
  sourcing a replacement, so this is a decision, not a seeding bug. Revisit if a suitable image
  turns up.

### M1 — catalog read API (M1.3)

Public, no authentication. Four routes under `/api/v1`: `GET /categories`, `GET /categories/{slug}`,
`GET /products`, and `GET /products/{slug}`. The detail route nests variants and the gallery; the
listing route deliberately does not, so a grid payload stays small.

Run it:

```bash
cd backend
uv run python manage.py migrate
uv run python manage.py seed
uv run python manage.py runserver
```

Then <http://localhost:8000/api/v1/docs> for Swagger, and
<http://localhost:8000/api/v1/openapi.json> for the schema `M1.4` generates types from.

Verify it:

```bash
uv run pytest tests/test_catalog_api.py -q

# 24 items on page one, "total": 46
curl -s "http://localhost:8000/api/v1/products" | head -c 300
# filters, sort, and paging share one query object
curl -s "http://localhost:8000/api/v1/products?category=lighting&sort=price&page_size=5"
```

Notes:

- Money is the `{"amount_cents", "currency"}` object everywhere (`API.md` section 1), including the
  `min_price` and `max_price` query parameters, which are integer cents.
- `page_size` caps at 100. A `page` below 1, a `page_size` outside 1–100, or an unknown `sort` is a
  `400` in the error envelope. A page past the end is an empty page, not a `404`.
- An unknown `category` *filter* returns zero results rather than erroring, so the storefront can
  render its explicit no-results state (`US-1.3`). An unknown *slug* on a detail route is a `404`.
- A `category` filter also matches descendants, so filtering by a parent includes its children.
- Don't trust Ninja's own error handling for the contract. Its defaults answer request validation
  with `422` and `{"detail": ...}`, and re-raise unhandled exceptions in production, producing a
  body that is not JSON at all. `core/errors.py` replaces all three handlers.
- Rows are read with `values()` rather than model instances, for the reason in section 8.

### M1 — frontend types from OpenAPI (M1.4)

The frontend's API types come from `frontend/openapi.json`, a committed snapshot of the schema. The
backend regenerates and verifies the snapshot; the frontend turns it into TypeScript locally, with
no network and no Python:

```bash
cd backend
uv run python manage.py export_openapi_schema   # writes ../frontend/openapi.json

cd ../frontend
pnpm codegen                                    # writes src/api/schema.d.ts
```

Verify it:

```bash
# from backend/ — the drift check Backend CI runs
uv run python manage.py export_openapi_schema
git -C .. diff --exit-code -- frontend/openapi.json

# from frontend/ — the generated types are covered by the normal gates
pnpm typecheck
```

Notes:

- **Only the snapshot is committed.** `src/api/schema.d.ts` is generated and gitignored, rebuilt by
  `pnpm dev`, `pnpm build`, and `pnpm typecheck`, so a fresh clone needs no extra step.
- **The snapshot lives in `frontend/`, not `backend/`, on purpose.** Vercel builds with `frontend`
  as its root directory, so a path pointing outside it would not exist during a deploy.
- **It is listed in `.prettierignore`.** Its bytes are owned by the export command and compared
  byte-for-byte by the drift check, and Prettier collapses short arrays onto one line — the two
  would disagree permanently and the check could never pass.
- **Changing the API means committing both halves** in one pull request: the code and the
  regenerated snapshot. Forget the second and the drift check fails, printing the diff.
- `frontend/openapi.json` is a path trigger for `Backend CI`, so hand-editing the snapshot fails
  too.
- The consumer of these types arrives at `M1.5`, which builds the catalog grid on them.

### M1 — catalog listing page (M1.5)

The first page to read the API. `/products` renders its heading from the static shell and streams
the grid, the result count, and the pager behind one `<Suspense>` boundary, so the page paints
immediately and the listing follows.

Run it:

```bash
cd backend
uv run python manage.py migrate
uv run python manage.py seed
uv run python manage.py runserver

cd ../frontend
pnpm dev
```

Then <http://localhost:3000/products>.

Verify it:

```bash
cd frontend
pnpm typecheck && pnpm lint && pnpm format:check && pnpm test && pnpm build

# ">46 products<" and 24 cards, "Page 1 of 2"
curl -s "http://localhost:3000/products" | grep -o '>[0-9]* products<'
# 22 cards on the last page
curl -s "http://localhost:3000/products?page=2" | grep -o 'Page [0-9]* of [0-9]*'
```

Notes:

- **`pnpm build` must report `/products` as Partial Prerender** (`◐`). That is the intended shape:
  a static shell with the listing streamed in. `○` would mean the fetch stopped happening, and
  `ƒ` would mean the boundary was lost.
- **The `<Suspense>` boundary is required, not stylistic.** With `cacheComponents: true`, an
  uncached fetch or a `searchParams` read outside a boundary is a build error, because neither can
  be resolved while the shell is prerendered. It is also the loading state `UX.md` section 5 asks
  for, which is why there is no `loading.tsx` — that would replace the heading along with the grid.
- **The listing is deliberately uncached.** `use cache` would let the grid join the static shell,
  but nothing invalidates the catalog yet, so a reseed would keep serving withdrawn products until
  the cache lifetime expired. Caching wants an invalidation story to go with it.
- **The pager is links, not buttons**, so paging works with no client JavaScript and the page
  number lives in the URL — the ground `US-1.4` needs for shareable filter state.
- **A page past the end renders the empty state with the pager intact.** The API answers such a
  page with an empty page rather than a `404` on purpose (`API.md` section 4); dropping the pager
  would strand a visitor who arrived on that URL.
- **`ProductCard` is not a link yet.** `US-1.1` asks for image, name, and price, and the detail
  route does not exist until `M1.6` — a link would point at a `404`.
- `in_stock` is in the payload but not the grid: availability belongs to the detail-page acceptance
  criteria (`US-1.2`), not the listing's.

### M1 — product detail page (M1.6)

`/products/{slug}` renders the gallery beside the price, availability, description, material,
colour and dimensions, plus the add-to-cart placeholder. Catalog cards now link here, which is the
link `M1.5` deliberately left out.

Run it:

```bash
cd backend
uv run python manage.py runserver

cd ../frontend
pnpm dev
```

Then open any card from <http://localhost:3000/products>.

Verify it:

```bash
cd frontend
pnpm typecheck && pnpm lint && pnpm format:check && pnpm test && pnpm build
```

Notes:

- **A missing slug answers `200`, not `404`, and that is deliberate.** The existence check runs
  inside the `<Suspense>` boundary so the shell and the skeleton survive, which means the response
  has already begun streaming by the time `notFound()` throws and the status cannot change. Next
  adds `<meta name="robots" content="noindex">` to compensate, and the docs recommend exactly this
  shape under "Calling `notFound()` after streaming has started". Verified: the tag is present on a
  missing product and absent on a real one. Blocking the route would buy a `404` status at the cost
  of the skeleton `UX.md` section 5 asks for.
- **`generateMetadata` costs no extra request.** Next memoises the underlying `fetch` across
  `generateMetadata` and the page. Verified by counting backend access-log lines for a single page
  view: exactly one.
- **The API client resolves `fetch` per call** rather than capturing it when the module loads,
  because Next replaces the global `fetch` to add that memoisation and a captured reference can
  predate the replacement.
- **Nothing is cropped, anywhere.** `ADR-0012` excludes `BY-ND` images "from any cropping or
  alteration", so both the gallery and the card use `object-contain`. The payload carries no licence
  for the UI to branch on, so the rule does not depend on the shipped set staying licence-clean. The
  source ratios are genuinely mixed (4:3, 3:2, 3:4, square, one 4.15:1), so expect letterboxing; that
  is the cost of staying licence-compliant. *(Corrected at `M1.9`: this bullet previously claimed 8
  of the 46 shipped images were `BY-ND`. They are not — see the `M1.9` note below.)*
- **The gallery renders one image**, because the source set holds one per product. Multi-image
  galleries are deferred rather than overlooked, and the component renders from the list, so more
  images is a data change.
- **The add-to-cart control is disabled, with its reason in visible text** and wired with
  `aria-describedby`. Nothing is specified for a placeholder, and the real behaviour belongs to
  `US-3.1` at `M3`. A disabled button that does not say why reads as broken.
- `dimensionParts` labels each dimension it renders, because the API's three are independently
  nullable and a bare `90 × 41` would not say which one is missing.

### M1 — search, filter and sort (M1.7)

`/products` now carries its whole state in the URL: `?q=`, `?category=`, `?min_price=`,
`?max_price=`, `?sort=`, `?page=`. A filtered, sorted, page-three view is a link someone can send,
and the back button walks back through what the reader actually did (`US-1.4`).

Verify it against the seeded catalog — every number below is measured, not guessed:

```bash
cd frontend
pnpm typecheck && pnpm lint && pnpm format:check && pnpm test && pnpm build

curl -s "http://localhost:3000/products?q=chair"           | grep -o '>[0-9]* products<'  # 3
curl -s "http://localhost:3000/products?q=zzzz"            | grep -o 'No products match'  # no-results state
curl -s "http://localhost:3000/products?category=textiles" | grep -o '>[0-9]* products<'  # 11
curl -s "http://localhost:3000/products?max_price=10000"   | grep -o '>[0-9]* products<'  # 11
curl -s "http://localhost:3000/products?sort=-price"       # first card renders $2,185.00
curl -s "http://localhost:3000/products?sort=price"        # first card renders $40.00
```

Notes:

- **The price bands are links, not form controls.** A band is *two* parameters (`min_price` and
  `max_price`), and a radio group or a `<select>` can submit only one value. Encoding the band as a
  single value would mean a second vocabulary for the URL that could no longer round-trip a
  hand-typed `min_price`/`max_price` — and the URL is the exact thing `US-1.4` requires to be
  shareable. So search, category and sort live in one GET form (which works with JavaScript off)
  and the bands are links carrying `API.md` section 4's own parameters.
- **The price bounds ride along as hidden inputs.** The form cannot display them, since they belong
  to the band links, so without this, typing a search term and pressing Apply would silently drop
  the price filter. Verified: `?min_price=75000` renders `<input type="hidden" name="min_price"
  value="75000">`.
- **Paging keeps the filters.** On a sorted view the Next link is `/products?sort=-price&page=2`.
  Without that, a shared page three would quietly show an unfiltered listing.
- **An unknown `category` is passed through, not validated away.** The API answers it with zero
  results rather than an error, and that is the explicit no-results state `US-1.3` asks for.
  Validating it in the storefront would turn that state into a silently unfiltered listing.
- **Anything the API would `400` on falls back rather than being sent** — a bad `sort`, a `page`
  below one, a negative bound. `?sort=cheapest&page=0&min_price=-5` renders all 46 products.
- **`SortSelect` submits its own form.** It is a client component only so a sort applies as soon as
  it changes; it calls `requestSubmit()` on the form rather than pushing a URL, so the navigation is
  the one the Apply button makes and the URL stays the single source of state. With JavaScript off
  the select waits for Apply, and nothing breaks.
- **The `<details>` panel is a deliberate part of `UX.md` section 8's mobile drawer**, open by
  default: a phone reader can collapse it and nothing needs JavaScript. The true overlay drawer —
  focus trap, scroll lock, focus return — is deferred to the `M6.2` accessibility pass, where it can
  be tested rather than guessed.

### M1 — home page (M1.8)

`/` renders a text hero and a featured row. The hero ships in the static shell; the row streams in
behind a `<Suspense>` boundary, which is why the route builds as Partial Prerender rather than static.

Verify it:

```bash
cd frontend
pnpm typecheck && pnpm lint && pnpm format:check && pnpm test && pnpm build

curl -s http://localhost:3000/ | grep -o 'Statement pieces'
curl -s http://localhost:3000/ | grep -oE '<h3[^>]*>[^<]*</h3>' | sed 's/<[^>]*>//g' | head -4
```

The featured row, in order, against the seeded catalog: Heia Ash Chest Of Drawers ($2,185.00), Heia
Birch Side Table ($1,881.00), Brisk Ash Dining Chair ($1,065.00), Ravn Birch Coat Rack ($872.00) —
one from each of Bedroom, Living Room, Dining Room and Storage.

Notes:

- **"Featured" is defined nowhere, so `M1.8` had to define it.** `US-1.5` says only "hero plus a
  featured grid", and the repository has no `is_featured` field, no API parameter and no curation
  rule — the word appears in the ROADMAP line, the story and one `UX.md` IA row, and nowhere else.
  The choice made here was to **derive** the row instead of adding schema: `selectFeatured` takes one
  piece per category from the priciest page of the catalog.
- **Why one per category.** The seed inserts category by category, so "newest four" would be four
  Decor pieces in a row, and "priciest four" would be two Bedroom and two Living Room pieces. One per
  category is what makes the row read as a range rather than a corner.
- **The row is labelled honestly rather than "featured"** — "Statement pieces", over "The
  highest-priced piece from each part of the collection". Calling a derived row "featured" would
  assert something about the catalog that nothing in the data supports.
- **Editorial curation, if it is ever wanted, is a backend task**: an `is_featured` column, a
  migration, a seed that marks products, and a `featured` filter on `/api/v1/products` — which also
  means regenerating and committing the OpenAPI snapshot. It is deliberately not hidden inside a page
  milestone.
- **The hero is text on purpose.** `US-1.5` asks for a "fast LCP", and text keeps the largest paint on
  a heading inside the static shell. It also avoids an LCP decision, a pick from the licence-clean
  set, and — because `ADR-0012` routes attribution to `/pages/credits` rather than inline — a silent
  attribution gap at the focal point of the page.
- **The home page has no `header`, `nav` or `footer`,** because none exists yet: `layout.tsx` renders
  only `<html><body>{children}</body></html>`, and the landmarks and skip link `UX.md` section 7 asks
  for are still outstanding. The page's own call to action is currently the only navigation on it.

### M1 — image credits page (M1.9)

`/pages/credits` renders the attribution for every shipped image — the licensing requirement
`US-6.1` carries as a `Must`. `M1.9` also added the endpoint the page reads: `GET /api/v1/credits`,
a new public catalog route returning all 46 credits unpaginated.

Verify it:

```bash
cd backend
uv run ruff format --check . && uv run ruff check . && uv run basedpyright && uv run pytest

cd ../frontend
pnpm typecheck && pnpm lint && pnpm format:check && pnpm test && pnpm build

curl -s http://localhost:8000/api/v1/credits | grep -oE '"total":[[:space:]]*[0-9]+'      # 46
curl -s http://localhost:3000/pages/credits | grep -c '<cite>'                            # 46 rows
curl -s http://localhost:3000/pages/credits | grep -oE '>[0-9]+<!-- --> <!-- -->images?<' # 46 images
```

The shipped licence mix, measured from the credits table: **33 `BY-2.0`, 11 `BY-SA-2.0`,
1 `CC0-1.0`, 1 `PDM-1.0`** — and no `BY-ND` at all.

Notes:

- **The attribution is read from the database, not from `manifest.csv` again.** `ADR-0012` keeps the
  manifest as the provenance record, but the page renders the `ImageCredit` rows the seed imported
  from it, so the page and the images cannot drift apart: a credit disappears when its image does.
  Parsing the CSV at build time would have made the frontend depend on a backend data file and let
  the two disagree.
- **`/api/v1/credits` is unpaginated on purpose.** `US-6.1` asks for every shipped image and the
  catalog ships 46, which belong on one page. `page_size` exists on `/products` because that list is
  a browse surface; this one is a legal annex.
- **Licence codes link to their Creative Commons deed.** `ADR-0012` settles for a page that
  "demonstrates licence awareness", and CC's attribution guidance asks for the licence to be linked
  to its deed wherever the medium allows — a bare `BY-SA-2.0` tells a reader which terms apply but
  not what they say. `lib/licences.ts` maps the four shipped codes; an unmapped code renders as plain
  text, because a guessed deed URL would claim terms the image does not carry. Note that the `CC0`
  and Public Domain Mark deeds live under `/publicdomain/`, not `/licenses/`.
- **Every "source" link is labelled for a screen reader.** Forty-six identical links reading
  "source" are indistinguishable in a link list, so each carries `aria-label="View the source of …"`
  — the same problem `UX.md` section 7 raises for repeated "Read more" links.
- **The page links back to the catalog and no further.** It is a legal annex, not a browse surface:
  `ADR-0012` routes attribution here rather than inline, so the cards and the detail pages stay
  clean.
- **A correction to the `M1.6` notes above.** They claimed 8 of the 46 shipped images were `BY-ND`.
  The vendored manifest does hold 100 rows, 8 of them `BY-ND` — but **none of those eight ship**:
  curation drops them, which is exactly what `ADR-0012` requires. The `object-contain` rule is
  unchanged and still the right rule; only its justification, and the gallery's own comment, were
  wrong, and both now say what is true. `backend/tests/test_catalog_api.py` now asserts that no
  shipped image is `ND`-licensed, so the claim cannot quietly become false again.
- **The route is `/pages/credits`, not `/credits`**, matching the `UX.md` section 4 row. `/credits`
  would sit beside `/products` as though it were a catalog surface.

### M2 — accounts models (M2.1)

`accounts` exists with the custom `User` model and `Address`, migrated. This is the milestone that
settles `AUTH_USER_MODEL`, so it is the one that would have been expensive to get wrong.

Verify it:

```bash
cd backend
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run   # "No changes detected"
uv run ruff format --check . && uv run ruff check . && uv run basedpyright && uv run pytest

uv run python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()
from django.contrib.auth import authenticate, get_user_model
user = get_user_model().objects.create_user(email='Ada@Example.COM', password='Correct-Horse-9!')
print(user.email)                                                          # ada@example.com
print(authenticate(email='ADA@EXAMPLE.COM', password='Correct-Horse-9!'))  # resolves
user.delete()
"
```

Notes:

- **`django.contrib.auth` was not installed before this milestone.** `INSTALLED_APPS` held only
  `contenttypes`, `staticfiles`, `core` and `catalog`, so no `auth_user` table had ever existed and
  no migration history referred to the default user. That is why `M2.1` is an *additive* migration
  rather than the database rebuild a late `AUTH_USER_MODEL` swap normally needs. Verified after
  `migrate`: `auth_user` does not exist, `accounts_user` does, and the 46 seeded products are
  untouched.
- **`citext` is replaced by lower-casing.** `DATA-MODEL.md` asked for a case-insensitively unique
  `email` and named Postgres's `citext` extension, which SQLite does not have. `UserManager`
  lower-cases the address on the way in, so uniqueness rests on an ordinary unique constraint
  instead of an extension — one less thing that behaves differently on the two backends.
- **`get_by_natural_key` is what makes sign-in case-insensitive.** `authenticate()` resolves the
  user through that method, so `ADA@EXAMPLE.COM` and `ada@example.com` reach the same row without
  every caller remembering to normalise the address first. Verified against the development
  database, not only in tests.
- **The default-address rule is a partial unique index, not application logic.** It renders as
  `CREATE UNIQUE INDEX unique_default_address_per_user ON accounts_address ("user_id") WHERE
  "is_default" = 1`. A second default is a real inconsistency rather than a display problem —
  checkout has to pick one address without asking which of the two defaults won — so the database
  refuses it. The index is per user, so two different users each having a default is correct, and
  one test exists only to keep it that way.
- **`AUTH_PASSWORD_VALIDATORS` is Django's four defaults.** `US-2.1` says "email + password with
  validation" without naming the rules, so the shipped defaults apply through `validate_password()`,
  which the register endpoint calls at `M2.2`. Measured: `12345` is rejected three times over, as
  too short, too common and entirely numeric.
- **`is_staff` currently selects nothing.** `django.contrib.admin` is not installed, so the column is
  a placeholder for the operator console `ADR-0007` settles on. It exists now because adding a column
  to a migrated table later is a migration for no reason.

### M2 — auth endpoints (M2.2)

`POST /auth/register`, `/auth/login`, `/auth/refresh`, `/auth/logout` and `GET /auth/me` are live
(`API.md` section 2, `ADR-0009`). The access token is a short-lived JWT in the response body; the
refresh token exists only as an httpOnly cookie scoped to `/api/v1/auth`.

Verify it:

```bash
cd backend
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
uv run ruff format --check . && uv run ruff check . && uv run basedpyright && uv run pytest

# The flow over HTTP, where cookie attributes actually mean something:
PORT=8392
uv run python manage.py runserver $PORT --noreload &
BASE=http://localhost:$PORT/api/v1
curl -sS -D - -c jar -X POST $BASE/auth/register -H 'Content-Type: application/json' \
  -d '{"email":"a@example.com","password":"correct-horse-9!"}'
curl -sS -b jar -c jar -X POST $BASE/auth/refresh    # rotates the cookie
```

Notes:

- **The refresh token is never in a response body.** A test asserts the cookie's value appears
  nowhere in the JSON, because "we only ever put it in the cookie" is the kind of claim that quietly
  stops being true.
- **Rotation and reuse detection.** Every refresh revokes the token it was given and mints a new one.
  A *revoked* token presented again means a copy is in circulation, so every live token for that user
  is revoked and the request is refused — a stolen token becomes a detectable event rather than a
  silent permanent session. Measured end to end: replaying an old cookie answered `401` and left the
  user with **0** live refresh tokens.
- **A `401` from `/auth/refresh` still clears the cookie, and that is not free.** Ninja's exception
  handler builds a *fresh* response, so a cookie cleared on the injected response and then abandoned
  by a `raise` never reaches the browser — and the browser would present a dead token on every page
  load forever. The endpoint therefore *returns* its `401` (`accounts/api.py::_fail`) instead of
  raising it. Found by a test, not by reading the code.
- **One message for every sign-in failure.** A wrong password and an unknown address return an
  identical code and message, so the endpoint cannot be used to enumerate registered addresses, and
  Django runs the password hasher even for an address with no account, so timing does not give it
  away either.
- **Token types are not interchangeable.** An access token presented to `/auth/refresh` is refused, so
  a stolen access token cannot extend its own life. The `typ` claim is required, not merely read.
- **`/auth/logout` needs a valid access token** (`API.md` section 2), so a client whose access token
  has already expired must refresh first. That is deliberate: the alternative is an unauthenticated
  endpoint that revokes sessions, which is a denial-of-service primitive.
- **The signing key defaults to `SECRET_KEY`.** Convenient locally and worth knowing about, because
  rotating one rotates both. `JWT_SECRET_KEY` overrides it.
- **Verified against PostgreSQL, not only SQLite.** The suite passes unchanged on both — 132 tests —
  and the difference between them is exactly the one that mattered: Django does not apply
  `SELECT ... FOR UPDATE` on SQLite, so the guard in `rotate()` cannot be exercised there at all.
  Measured on Postgres, with one process holding the row lock for 5s: `rotate()` **blocked 3.52s** and
  returned only once the holder committed. The guard is real, so the outstanding risk recorded at
  `M2.2` is closed.
- **Two concurrent refreshes with one cookie sign the user out, deterministically.** The lock
  serialises them, so this is not a race with a random outcome: the first rotates and answers `200`,
  and the second arrives to find the token revoked, takes the reuse path and answers `401`. Because
  reuse revokes *every* live token for the user, the winner's fresh token dies with it — observed end
  to end as `refresh A: 401 | refresh B: 200`, leaving **0** live tokens. A user with two tabs
  refreshing at once is logged out. This is the conservative reading of `ADR-0009`; the alternative is
  a grace window on a just-rotated token. Recorded as `QA-G4` rather than changed here, because it
  needs a decision before the frontend holds sessions at `M2.4`.
- **Running against Postgres locally.** `docker compose up -d db`, then copy `.env.example` to
  `backend/.env`, which sets `DATABASE_URL`; leaving it empty falls back to `backend/db.sqlite3`.
  `manage.py migrate` and `manage.py seed` have both been run against the container, and the seeded
  counts match SQLite exactly: 7 categories, 46 products, 95 variants, 46 images, 46 credits.
  `Docker Postgres` means the psql client can be used directly:
  `docker exec lysheim-db-1 psql -U lysheim -d lysheim`.
- **Not protected by a rate limit at `M2.2`,** which is what `M2.3` added — see the next entry.

### M2.3 — rate limiting and the refresh origin guard

Every auth endpoint carries a limit (`US-2.2`, `NFR-3`), and `/auth/refresh` checks the request's
origin before it reads the cookie (`ADR-0009`). Verify it:

```bash
cd backend
uv run ruff format --check . && uv run ruff check . && uv run basedpyright && uv run pytest

# Over HTTP, where a throttle lives in the process's own cache and a forged header has to be ignored:
PORT=8390
uv run python manage.py runserver $PORT --noreload &
BASE=http://localhost:$PORT/api/v1
for i in $(seq 1 12); do
  curl -sS -o /dev/null -w "%{http_code} " -X POST $BASE/auth/login \
    -H 'Content-Type: application/json' -d '{"email":"a@example.com","password":"wrong"}'
done; echo                          # ten 401s, then 429 with a Retry-After
curl -sS -o /dev/null -w "%{http_code}\n" -X POST $BASE/auth/login \
  -H 'Content-Type: application/json' -H 'X-Forwarded-For: 198.51.100.99' \
  -d '{"email":"a@example.com","password":"wrong"}'   # still 429: the header proves nothing
```

Notes:

- **The limits are per client, not per account.** Keying on the submitted address would let anyone
  lock a known account out of its own sign-in screen, which turns a rate limit into a denial-of-service
  tool. The anonymous endpoints key on the client IP; the authenticated ones key on the account. The
  cost is that a distributed attack is not meaningfully slowed by this alone — a deliberate trade.
- **The limit applies to the endpoint, not to failures.** Once the window is exhausted a *correct*
  password is refused too, until it passes. Measured: ten rejections, then `429` with `Retry-After: 51`
  — and the right password also answered `429`.
- **The rate is re-read on every request, deliberately.** `SimpleRateThrottle.__init__` resolves the
  rate once and stores the parsed numbers on the instance, and Ninja attaches throttle *instances*
  built at import — so Ninja's own throttles would freeze whatever the settings held when the module
  was imported. A test found this by failing: a lowered limit simply did not apply.
  `accounts/throttling.py` overrides `get_rate` to read `NINJA_DEFAULT_THROTTLE_RATES` per request, so
  a limit is a setting rather than a constant.
- **`NINJA_NUM_PROXIES` is not optional.** Ninja uses `X-Forwarded-For` verbatim when it is unset, so
  any client could invent a fresh identity per request and never be limited at all. It is `0` locally,
  where nothing sits in front of uvicorn, and `1` in production, because Render's load balancer
  terminates TLS and forwards to a port that is not directly reachable. Both directions are failures:
  too high and the header is forgeable again, too low and every visitor shares one bucket, so a single
  abuser locks out everyone. Verified over HTTP: two different forged `X-Forwarded-For` values were
  both answered `429`, while a request bound to a second loopback address got its own window.
- **The store is the Django cache, which is per process.** The limits are therefore per worker and
  reset on deploy. That is correct for one uvicorn process and wrong the moment there is more than one;
  point `CACHES` at a shared backend first (`CACHE_BACKEND`, `CACHE_LOCATION`). Tracked as `QA-G6`.
- **The origin guard only refuses when it can tell.** `Origin` is the header read, with `Referer` as a
  fallback. A request presenting neither is allowed, because that is curl or a future mobile client,
  and no page can stop a browser from sending one. The origin must match `CORS_ALLOWED_ORIGINS`, so an
  environment that forgets to set it refuses every browser refresh — the safe direction to fail in.
  Verified: a foreign `Origin` and a foreign `Referer` both answered `403` `FORBIDDEN`, the next
  trusted refresh still answered `200`, and a request with no origin at all was allowed.

### M2.4 — the frontend session and cross-origin access

The browser keeps the access token in memory, gets a new one silently when it expires (`US-2.3`), and
can reach the API at all only because of the CORS configuration added here. Verify it:

```bash
cd backend
uv run ruff format --check . && uv run ruff check . && uv run basedpyright && uv run pytest
cd ../frontend
pnpm format:check && pnpm lint && pnpm typecheck && pnpm test && pnpm build

# The headers a browser needs, over HTTP:
cd ../backend
PORT=8388
uv run python manage.py runserver $PORT --noreload &
curl -sS -i -X OPTIONS "http://localhost:$PORT/api/v1/auth/refresh" \
  -H 'Origin: http://localhost:3000' \
  -H 'Access-Control-Request-Method: POST' \
  -H 'Access-Control-Request-Headers: content-type' | head -12
```

Notes:

- **The access token lives in a module variable and nowhere else.** Not `localStorage`, not
  `sessionStorage`, not a cookie — anything a script can read, an injected script can read, which is
  what `ADR-0009` rejected. The cost is that a reload loses it, so "no token" is *not* the same as
  "signed out": `SessionProvider` renews once on mount and the UI has three states — `restoring`,
  `authenticated`, `anonymous` — so the header cannot flash "Sign in" at a signed-in customer on every
  navigation.
- **One refresh at a time, for the whole app.** A correctness guard, not a cache. The API rotates
  refresh tokens and treats a second use of an old one as theft, revoking *every* session for the
  account. Two protected requests that 401 together — or a page-load restore racing a retry — would
  therefore sign the customer out of everything. `lib/session.ts` holds one in-flight promise that
  every caller shares, and two tests exist for that alone: two concurrent 401s, and a restore
  overlapping a retry. The second of those failed when it was first written, for a reason worth
  keeping: the mocked refresh resolved instantly, so the two never overlapped, and a browser cannot
  produce that sequence because its refresh is a network call.
- **CORS was missing entirely until now.** The `CORS_ALLOWED_ORIGINS` setting had existed since
  `M0.6`, but nothing read it on the response path, so a browser could not have called this API.
  `django-cors-headers` now supplies the middleware, placed above `CommonMiddleware` so it answers
  the preflight before anything else can, with `CORS_ALLOW_CREDENTIALS` on because the refresh token
  travels in a cookie.
- **The allow-list is load-bearing in two places, deliberately.** `CORS_ALLOWED_ORIGINS` decides who
  may *read* a response (the browser enforces that) and is also the list the refresh origin guard
  compares against (the API enforces that). One list, so the two cannot disagree. It is empty by
  default, so a deployment that forgets it fails closed: cross-origin calls stop working and every
  browser refresh is refused.
- **Verified over HTTP:** both preflights answered `200`, with `authorization` and `content-type`
  among the allowed headers; a registration from the storefront origin answered `201` and was
  readable, setting exactly one refresh cookie; the silent refresh answered `200` and rotated exactly
  one cookie; and an unlisted origin received no allow-origin header at all while the same origin's
  refresh was refused `403` by the guard. 0 tracebacks, 0 `500`s.
- **What this did not prove.** The interceptor is JavaScript, and the headers being right is not the
  browser behaving correctly. That needs a page to click, so it is `M2.5`'s check (`QA-C43`); the unit
  tests cover the logic and the HTTP check covers the headers, and neither substitutes for the other.

### M2.5 — the sign-in and registration pages

`/login` and `/register` are the first pages that write to the API, and the header now reflects the
session instead of always offering a link. Both pages are generated as static HTML: they are identical
for everyone, because whether anyone is signed in is decided on the client, from a token that only
exists in memory. Verify:

```bash
cd frontend
pnpm format:check && pnpm lint && pnpm typecheck && pnpm test && pnpm build

# The two shapes of a field error, and the sentence the form shows, over HTTP:
cd ../backend
PORT=8399
uv run python manage.py runserver $PORT --noreload &
BASE=http://localhost:$PORT/api/v1
curl -sS $BASE/auth/register -H 'Content-Type: application/json' \
  -d '{"email":"m25@example.com","password":"a-strong-one-9x","display_name":"M"}'; echo  # 201
curl -sS $BASE/auth/register -H 'Content-Type: application/json' \
  -d '{"email":"m25@example.com","password":"a-strong-one-9x"}'                         # taken
curl -sS $BASE/auth/login -H 'Content-Type: application/json' \
  -d '{"email":"m25@example.com","password":"wrong"}'                                   # 401
```

Notes:

- **One form, two pages.** `AuthForm` takes a mode. Two components would have duplicated the part
  worth having in one place: mapping the API's field errors onto inputs, the form-level message, the
  busy state, and the rule that the server's answer replaces whatever the client guessed.
- **The server names a field differently, and the form knows it.** The API calls it `display_name`
  and the input is `displayName`, so the mapping is written out rather than relying on the two
  happening to agree — which is exactly the coincidence that stops holding the moment a field is
  renamed.
- **A server field name carries its source, and is not an input name.** A rejected body comes back as
  `body.email`: precise about *where* the error is, useless as a DOM id. The mapper strips
  `body.`/`query.`/`path.` and falls back to the form-level message when a name matches no input, so
  an error is never dropped silently — a field error with nowhere to land looks like nothing happened
  at all. **`API.md` §3 documented this wrongly** (a bare `email`); the check over HTTP caught the
  difference, so the contract now matches the code and both shapes are handled.
- **Client-side validation is a courtesy, not the gate.** The rules in `lib/auth-form.ts` mirror the
  published ones so obvious mistakes are caught before a round trip. The API still decides, and on a
  rejection its `details` are what get displayed, so the client cannot call something valid that the
  server refuses.
- **Accessibility comes from the markup, not from colour.** Every input has a real `<label for>`, the
  message sits in that field's own block with `aria-describedby` pointing at it and `aria-invalid`
  set, and the form-level failure is a `role="alert"`. The error is a sentence in the flow, because
  `SCOPE.md` NFR-2 forbids signalling by colour alone.
- **`noValidate`, and no `required`.** The platform's validation bubble would appear first and say
  something different from every other message on the page. Taking the form over means one voice, and
  the messages become testable in `auth-form.test.ts` instead of belonging to the browser.
- **The header has three states, not two.** The access token lives in memory, so on first paint the
  app genuinely does not know whether the visitor is signed in. `restoring` exists so the header stays
  neutral rather than showing "Sign in" to a signed-in customer and snatching it back a moment later.
- **Sign-out tells the API first, then forgets.** `ADR-0009` requires the refresh token to be
  invalidated server-side, so the request goes first and the local store is cleared in a `finally`
  whatever comes back. A logout that failed because the token was already dead has still logged the
  user out, and a signed-in header over an API that refuses every call would be worse than either.
- **Verified:** both pages answered `200` with the form already in the HTML, the register password
  field carrying `autocomplete="new-password"`; the header rendered no session state; a duplicate
  address came back as `body.email` and a weak password as `body.password`; a failed sign-in returned
  `401` `UNAUTHENTICATED` with the sentence the form shows. 0 tracebacks, 0 `500`s, 0 web errors.
- **What this did not prove.** All of the above is the HTML the server sends; the behaviour it
  triggers is JavaScript in a browser. The four browser cases — validation before a request goes out,
  the `429` message, the silent restore, and sign-out — are `QA-C48`–`QA-C51`, not run until someone
  drives a real browser.

### M2.6 — the profile and the address book

`PATCH /auth/me` edits the display name (`US-2.4`) and `/addresses` is the delivery book (`US-2.5`),
with `/account` as the screen for both. Every route acts only on the token holder's own rows, and
every screen shows only what the token holder's own rows contain. Verify:

```bash
cd backend
uv run ruff format --check . && uv run ruff check . && uv run basedpyright && uv run pytest

# The ownership rule over HTTP: a second account must not see or touch the first one's address.
PORT=8401
uv run python manage.py runserver $PORT --noreload &
BASE=http://localhost:$PORT/api/v1
ADA=$(curl -sS $BASE/auth/register -H 'Content-Type: application/json' \
  -d '{"email":"m26.ada@example.com","password":"correct-horse-9!"}' | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')
curl -sS -H "Authorization: Bearer $ADA" -H 'Content-Type: application/json' $BASE/addresses \
  -d '{"recipient":"Ada Lovelace","line1":"12 Analytical Way","city":"London","postal_code":"N1 9AB","country":"GB"}'
# -> 201, "is_default": true, and the optional fields defaulted to ""
```

Notes:

- **Ownership is held by the query, not by a comparison.** Every route reads
  `Address.objects.filter(user=request.auth, pk=...)` rather than fetching by primary key and then
  checking the owner, so somebody else's row is simply not found and there is no branch in which the
  check can be omitted. `QA-C31` is that failure; the tests assert both that the row is unreachable
  *and* that it is untouched after a refused request.
- **`404`, not `403`, for another account's address.** `403` confirms that the id exists, which is
  precisely what an attempt to enumerate addresses is trying to learn.
- **`filter(user=...)` rather than `user.addresses`.** The reverse accessor is invisible to
  `basedpyright` (`ADR-0014`), and the explicit query is also what makes the owner part of the lookup
  rather than a following check — one decision, two reasons.
- **Exactly one default, which is stronger than the database promises.** `DATA-MODEL.md`'s partial
  unique index enforces *at most one* default per user; these routes hold *exactly one* while the
  account has any address, so checkout never has to ask which of several defaults won. The first
  address becomes the default whether or not the client asked, promoting another demotes the previous
  one, and deleting the default promotes the oldest survivor.
- **Clearing the default is a `409`, not a `400`.** The body is well-formed and it is the state of the
  resource that refuses it. `400` is what the frontend maps onto form fields, so reusing it would put
  a sentence about defaults onto an input the customer just edited. Verified over HTTP.
- **The required fields have a floor of one character.** The model declares them non-blank and nothing
  in the database refuses `recipient = ""`, so the schema refuses it — the same class of hole `M1.2`
  found with `max_length` on SQLite.
- **A bug the new tests found, in the error envelope.** Pydantic's errors arrived as
  `body.payload.country` — Ninja inserts the *view parameter's* name into the location — while a
  `ValidationError` raised by hand produces `body.email` from the same endpoint. One contract with two
  spellings: a client that strips the source prefix, as `API.md` §3 tells it to, would match one shape
  and quietly fall back to a form-level message for the other. `core/errors.py` drops that segment now
  and a test pins both paths. It is worth knowing *why* it lasted: every field-error test until now
  asserted the hand-raised path, so no test had ever looked at a pydantic-generated body error.
- **`ninja.Status` rather than a `(status, body)` tuple.** Ninja 1.7 deprecates the tuple, and the
  warning appeared 28 times in a single test file.
- **Verified over HTTP, against PostgreSQL:** the first address is created `201` and default, a second
  is not, the list puts the default first, promoting moves the default while exactly one remains,
  clearing it answers `409` `CONFLICT`; a second account sees `[]` and gets `404` on `PATCH` and
  `DELETE`, with the first account's rows unchanged afterwards; deleting the default promotes the
  oldest survivor; `PATCH /auth/me` edits the display name and an empty body leaves it alone; and all
  three field-error shapes report `body.<field>`. 0 tracebacks, 0 `500`s.
- **The screens are two sections on one route.** `UX.md` section 3 gives `/account` and no more, so
  the profile and the address book are two `<section>`s there rather than two routes. The page is a
  Server Component — heading, title, frame — wrapping one client component, because everything inside
  it is behind a token that only exists in memory (`ADR-0009`). It builds as **static** (`○`).
- **The consequence of that, stated plainly:** a visitor without JavaScript sees "Loading your
  account…" and nothing else, forever. The alternative — having the server send the signed-out state
  — would flash "not signed in" at a signed-in customer on every navigation, which is a lie told to
  a real customer to tidy up a case where no session is even possible. Verified: the signed-out copy
  is absent from the server HTML.
- **`defaultControl` is a three-way decision, not a boolean.** The add form offers the checkbox only
  when the account already has an address; for the first address it shows a sentence instead, because
  the API makes the first one default whether or not anyone asks and a checkbox there could not do
  anything; editing shows neither, because `API.md` section 8 refuses to let a default be cleared.
  `toUpdatePayload` therefore emits no `is_default` key at all — a save cannot try to unset it.
- **The default is presented as a word.** `Default` is a badge beside the heading, not a highlight:
  `SCOPE.md` NFR-2 forbids encoding state by colour alone, and "which one will checkout use" is the
  one thing this list is scanned for.
- **Two shared modules came out of the second form.** The envelope reader and the field-name mapper
  moved from `lib/auth-form.ts` to `lib/api-failure.ts`, and the labelled input became
  `components/text-field.tsx` — the accessibility wiring (`aria-invalid` plus `aria-describedby`) is
  the part that must not drift between forms. `required` and `maxLength` are still deliberately
  absent for the reasons that file records.
- **A lint rule to know about.** `react-hooks/set-state-in-effect` fails the mount fetch if it is
  called directly, even though its state lands after the await. Wrapping it in the async IIFE — the
  shape `session-provider` already uses — is what it accepts, and it means the same thing.
- **The check found its own bug, and it is the interesting kind.** The "no session-bound content in
  the server HTML" assertion first searched for the words `Profile` and `Addresses`. Both appear in
  the page's meta description as prose, so it reported two rendered sections that were not there.
  It now matches the section ids. The page was right, the check was wrong, and a passing check that
  passes for the wrong reason is worth catching in the same session it was written.
- **A script bug worth not repeating.** The first version of the end-to-end script killed the `pnpm`
  process it backgrounded, which is not the process holding the port: `pnpm start` runs `next start`
  as a child, and the child survived. The script uses `setsid` and `kill -- -$PID` now, so the whole
  group goes. Also: it must not be pointed at ports 3000 or 8000 if the development instance is
  running — it refuses to start rather than taking them, which is how this was noticed.
- **Verified over HTTP:** `/account` answered `200` with one `<h1>` and its own title, carrying the
  restoring state and not the signed-out copy, with 0 `<h2>` elements in the shell; a body built as
  the add form builds it answered `201` and became the default unasked; the edit shape (no
  `is_default`) answered `200` and left it default; `PATCH /auth/me` answered `200`; the list came
  back default-first; `/`, `/products`, `/login`, `/register` and `/pages/credits` are unregressed;
  0 tracebacks, 0 `500`s, 0 web errors. The interactive cases are `QA-C56`–`QA-C62`, recorded as not
  run because they need a browser.

## 7. Deployment

`M2.7` deploys the walking skeleton — a public URL serving the catalogue and auth. `M7` completes it
(custom domains, backups, the production journey over a real customer path). What follows is the
procedure `M2.7` establishes, written to be followed rather than admired.

### 7.1 What runs where

| Piece | Host | Consequence |
| --- | --- | --- |
| API | Render, free web service, Docker | `runtime: docker` builds `backend/Dockerfile`. Render has no compose runtime — `docker-compose.yml` is not one of its service types — so `compose.yml` stays a **local** tool and the Dockerfile is the only thing the two share. |
| Web | Vercel | Next.js, root directory `frontend`. |
| Database | Supabase, free | Reached through the **shared pooler** (7.3). |
| Images | Vercel | All 46 are vendored in `frontend/public/images/`, so Django serves no media and no static files: no `collectstatic`, no WhiteNoise, no object storage in this milestone. |

`render.yaml` in the repository root is the API as configuration. Four fields carry weight:

- **`dockerCommand` names one file and nothing else.** It is a string Render *parses*: it strips a
  leading `/bin/sh -c` and runs the remainder through its own shell, which is why the compound command
  that used to live here — quoted, as holding `&&` requires — became a single unfindable word and
  failed the first deploy (7.4 and section 8). It now points at `/app/docker-entrypoint.sh`: one
  token, nothing to strip, nothing to quote. The Dockerfile's `CMD` is the same script, so the image
  also starts correctly on a host that ignores this field.
- **`sync: false`** makes Render prompt for a value in the Dashboard and never store it in the file.
  That is what lets a Blueprint be committed while the secrets are not.
- **`generateValue: true`** makes Render invent a 256-bit value and keep it across syncs.
  `DJANGO_SECRET_KEY` uses it, so no human ever handles that key.
- **`DJANGO_ALLOWED_HOSTS` from `RENDER_EXTERNAL_HOSTNAME`** lets the service tell itself its own
  hostname, which removes a manual step and a class of `400 DisallowedHost`. A custom domain added
  later still has to be appended by hand.

The file validates against Render's published schema, which is also served to editors through
SchemaStore: `curl -sS https://render.com/schema/render.yaml.json` and check it with `jsonschema`
before trusting a change to it, because a misspelled field is silently ignored by the platform and
the service simply behaves as if it were absent.

### 7.2 Credentials: `.env` locally, the dashboard in production

`.env` is one *local* way to fill the process environment; in production the platform fills it. The
code does not know the difference, and three verified facts make that true rather than aspirational:

- `django-environ`'s `read_env()` does **not** overwrite variables that already exist
  (`backend/config/settings/base.py`), so a dashboard variable beats a file. There is one code path,
  not two.
- `.gitignore` ignores `.env` and `.env.*` and un-ignores `.env.example`, and both `.dockerignore`
  files exclude `.env` — so a local `.env` can reach neither the repository nor the image. Only the
  *keys* are committed.
- Three `.env` files locally, for three consumers: `backend/.env` (the API), `frontend/.env.local`
  (the web app), and a root `.env` (Docker Compose's own `${...}` substitutions in `compose.yml`).
  Confusing these is the usual local mistake; the cloud side is the simpler half.

On the frontend, `NEXT_PUBLIC_API_BASE_URL` is **public**: Next inlines `NEXT_PUBLIC_*` into the
browser bundle at build time, so nothing secret may ever carry that prefix, and changing the value
needs a redeploy rather than a restart.

### 7.3 Order

Ordered, because of one dependency: `CORS_ALLOWED_ORIGINS` needs Vercel's URL and Vercel's
`NEXT_PUBLIC_API_BASE_URL` needs Render's. Naming the Render service first breaks the circle, since a
service called `lysheim-api` is reachable at `https://lysheim-api.onrender.com`.

1. **Supabase.** Create the project in the region that matches Render's, and copy the **shared
   pooler, session mode** string from Connect:
   `aws-<n>-<region>.pooler.supabase.com:5432`, with `?sslmode=require`. Not the direct connection:
   that resolves to IPv6 only on the free plan while Render's free tier is IPv4 only, and the symptom
   is a "no route to host" on the first query.
2. **Render.** New → Blueprint → this repository. Render reads `render.yaml` and prompts for
   `DATABASE_URL` (the pooler string) and `CORS_ALLOWED_ORIGINS` (Vercel's URL, if known; it can be
   edited and redeployed later). Watch the first deploy's log for the migration and seed output.
3. **Vercel.** Import the repository, root directory `frontend`, and set
   `NEXT_PUBLIC_API_BASE_URL=https://lysheim-api.onrender.com` for **Production** *before* the first
   build, then deploy. Setting it afterwards does nothing until the next build.
4. **Close the loop.** Put Vercel's production URL into Render's `CORS_ALLOWED_ORIGINS` — the exact
   origin, scheme included, no trailing slash — and let Render redeploy.
5. **Smoke journey.** 7.5.
6. **Keep-alive.** `ADR-0011` accepts cold starts and mitigates them with a periodic ping. Whatever
   does the pinging is an external account and a founder decision; until then the first visit after
   idle is slow and is not a bug.

### 7.4 Why migrations run in the start command

Render's pre-deploy command is for paid instance types, and this service is free, so there is no
separate stage to run migrations in. Render's own Docker documentation suggests folding them into the
start command, and this repository already used that shape locally — `compose.yml` runs
`sh -c "python manage.py migrate --noinput && uvicorn ..."`.

**That shape belongs in a file, not in a YAML field.** Copying the one-liner into Render's "Docker
Command" failed the first deploy of `M2.7`: Render strips a leading `/bin/sh -c` from that field and
hands the rest to its own shell, so the double quotes holding the `&&` switch together made the whole
command a single word —

```
python manage.py migrate --noinput && python manage.py seed && exec uvicorn … --port 10000: not found
```

The compound command now lives in `backend/docker-entrypoint.sh` (`migrate`, then `seed`, then
`exec uvicorn … --port "${PORT:-8000}"`), and `render.yaml` names that file with one token. `exec` is
not decoration: it hands the platform's `SIGTERM` to uvicorn rather than to a shell that would sit out
the shutdown delay and never pass it on.

Verified by building the image and booting it against an **empty** PostgreSQL with `PORT=9999` — the
production path, minus Render. Note the published port rather than `--network host`, which on Docker
Desktop binds inside its VM and is then unreachable from the host:

```bash
docker run -d --name m27-pg -p 5599:5432 -e POSTGRES_USER=lysheim \
  -e POSTGRES_PASSWORD=lysheim -e POSTGRES_DB=lysheim postgres:17-alpine

docker build -t lysheim-api-m27 ./backend
docker run -d --name m27-api -p 9999:9999 --add-host=host.docker.internal:host-gateway \
  -e PORT=9999 -e DJANGO_ENV=prod \
  -e DJANGO_SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))') \
  -e DJANGO_ALLOWED_HOSTS=localhost -e NINJA_NUM_PROXIES=1 \
  -e DATABASE_URL=postgres://lysheim:lysheim@host.docker.internal:5599/lysheim lysheim-api-m27

curl -s -o /dev/null -w '%{http_code}\n' localhost:9999/healthz   # 200 — and it must not redirect
```

The first boot applied all 19 migrations to nothing, seeded 46 products and 7 categories, and bound
9999 rather than 8000; `/healthz` answered `200`, and a product request carrying
`X-Forwarded-Proto: https` answered `200` with real rows. The second boot — the shape every wake takes
— found nothing to migrate, re-ran the seed as a no-op, and was serving about 9s after `docker run`,
most of that container start rather than work.

Measured on a throwaway database, so the dev database was untouched:

| Step | Cold | On every wake after |
| --- | --- | --- |
| `migrate` | 1.18s | 0.74s |
| `seed` (46 products) | 0.98s | 0.91s |

Almost all of that is Django's interpreter boot (about 0.65s floor per command); the work itself is a
quarter of a second. Against a cold start measured in tens of seconds it is noise.

Three things hold this up, and each can stop being true:

- **`seed` is idempotent by contract** — `core/management/commands/seed.py` wraps the whole run in one
  transaction. **Never put `--reset` in the start command:** it clears the seeded rows first, so every
  cold start would wipe the catalogue.
- **Migrations are not safe to run concurrently**, and this shape assumes one instance. The free plan
  runs one with no autoscaling, which is why it is accepted rather than guarded (`QA`-level decision,
  recorded here on purpose). If the service ever scales, or if `M7` moves it to a paid plan where
  zero-downtime deploys overlap two instances, take an advisory lock before migrating.
- **`initialDeployHook`** (alias `afterFirstDeployCommand`) is the tidier home for the seed: Render
  runs it once after the first successful deploy. The Blueprint spec does not mark it plan-restricted,
  but unlike the pre-deploy restriction that is documented, this is not — so treat it as an
  improvement to try, not a fact.

### 7.5 The smoke journey

Pointed at the two public hosts, and worth running on every deploy that touches configuration:

```bash
API=https://lysheim-api.onrender.com
WEB=https://lysheim.vercel.app          # the real production URL

curl -sS "$API/healthz"                                    # {"status": "ok", ...}
curl -sS -o /dev/null -w '%{http_code}\n' "$WEB/"          # 200
curl -sS -o /dev/null -w '%{http_code}\n' "$WEB/products"  # 200

TOKEN=$(curl -sS "$API/api/v1/auth/register" -H 'Content-Type: application/json' \
  -d '{"email":"smoke@example.com","password":"correct-horse-9!"}' \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')
curl -sS "$API/api/v1/addresses" -H "Authorization: Bearer $TOKEN"
```

Then the three things only a real deployment can show, none of which a local stack can:

```bash
# 1. The refresh cookie's attributes, which is what makes the cross-site call work at all.
curl -si -X POST "$API/api/v1/auth/login" -H 'Content-Type: application/json' \
  -d '{"email":"smoke@example.com","password":"correct-horse-9!"}' \
  | grep -i '^set-cookie'          # expect: Secure; HttpOnly; SameSite=None; Path=/api/v1/auth

# 2. The rate limit, which must count the real client and not Render's balancer.
for i in $(seq 1 11); do
  curl -sS -o /dev/null -w '%{http_code} ' -X POST "$API/api/v1/auth/login" \
    -H 'Content-Type: application/json' -d '{"email":"smoke@example.com","password":"wrong"}'
done; echo                                       # expect: ten 401s then 429

# 3. The CORS preflight from the real origin.
curl -si -X OPTIONS "$API/api/v1/addresses" -H "Origin: $WEB" \
  -H 'Access-Control-Request-Method: GET' | grep -i 'access-control-allow-origin'
```

`NINJA_NUM_PROXIES=1` is what makes check 2 pass: at `0` every visitor shares one bucket, and at an
unset value Ninja trusts a client-supplied header that anyone can forge. Delete the smoke account
afterwards — `manage.py shell`, or a local `DATABASE_URL=<pooler> .venv/bin/python manage.py shell`.

### 7.6 If the first deploy fails

Anticipated rather than observed, so this is the order to check them in:

- **`400 DisallowedHost` on every request.** `DJANGO_ALLOWED_HOSTS` did not resolve. The
  `RENDER_EXTERNAL_HOSTNAME` reference in `render.yaml` is the likely cause; replace it with the
  hostname as a plain value.
- **`ImproperlyConfigured: DJANGO_SECRET_KEY must be set in production`.** `prod.py` refusing to boot
  with the development key, which is the guard working. The `generateValue` field is missing.
- **Browser requests fail while `curl` works.** CORS: `CORS_ALLOWED_ORIGINS` is empty or holds an
  origin that does not match exactly (a trailing slash or the `www` host is enough). The API answers
  `400` for a refresh from an unrecognised origin by design.
- **Signed in, then signed out on reload.** The refresh cookie is not surviving the cross-site call:
  both sides must be HTTPS, and `prod.py` must be in play rather than `dev.py`.
- **"No route to host" from the API to the database.** The direct Supabase connection instead of the
  shared pooler — IPv6 versus IPv4, per 7.3 step 1.
- **The health check never passes.** The command is not binding `$PORT`, which `dockerCommand` handles
  with `${PORT:-8000}`; if that field is ever removed, the Dockerfile's hardcoded 8000 is what
  remains.
- **The first request after a quiet spell takes a minute.** A cold start, not a fault (`ADR-0011`).

### 7.7 Accepted, with the reason

- **Cold starts.** The price of zero running cost, mitigated by a keep-alive ping when one exists.
- **One instance.** Which is also what makes the per-process throttle cache correct: `base.py` warns
  that more than one worker means each allows the full rate on its own.
- **`X-Forwarded-Proto` is trusted, and `/healthz` is exempt from the HTTPS redirect.** Both are in
  `prod.py`, and both are load-bearing. Without the first, `SECURE_SSL_REDIRECT` would bounce every
  request — including ones that arrived over HTTPS — in a loop, because the balancer forwards plain
  HTTP. The container test showed the pair precisely: `301` to the `https://` URL with no header,
  `200` with it. The exemption exists because a health probe is not a browser and has nothing to
  upgrade to, so the probe answers `200` over either scheme and a redirect can never be the reason a
  deploy fails to come up. Trusting the header is safe for the same reason `NINJA_NUM_PROXIES = 1` is:
  the app is not reachable except through the balancer.
- **`CONN_MAX_AGE` is not set.** `ADR-0011` says the pooler is used "with `CONN_MAX_AGE` tuned
  accordingly", but nothing sets it, so it is Django's default of `0` — which is the right value
  behind a pooler, since a persistent connection would sit in a pooled slot it does not need. The
  setting is correct by omission; the ADR's wording implies a knob that does not exist.

### 7.8 The deployment as it stands

| | |
| --- | --- |
| Web | <https://ecommerce-project-five-psi.vercel.app> |
| API | <https://lysheim-api.onrender.com> |
| Data | Supabase, shared pooler in session mode |

Deployed 2026-10-12, and verified **from outside the stack** — which is the only vantage point for
some of it, because every test and every `docker compose up` in this repository passes while the
wiring is wrong. The checks, and what each one actually asserts:

| Check | Result | The assertion |
| --- | --- | --- |
| `GET /healthz` | `200`, request id | the container is up and bound `$PORT` |
| `GET /api/v1/products` | `200`, 46 products | the pooler string, migrations and seed all work |
| `GET http://…/healthz` | `301` → `https` | TLS is enforced before Django sees it |
| Response headers | HSTS `includeSubDomains; preload`, `nosniff`, `strict-origin-when-cross-origin` | `prod.py`'s hardening is applied, not merely written |
| Preflight, real origin | `access-control-allow-origin: https://ecommerce-project-five-psi.vercel.app` | CORS is configured for the deployed frontend |
| Preflight, foreign origin | **no** `access-control-allow-*` header | it answers `200` and the browser refuses it; the header is the assertion, not the status |
| `GET /api/v1/addresses`, no token | `401` | auth is enforced in production, not only in tests |
| `POST /api/v1/auth/refresh`, foreign origin | `403` | the `M2.4` origin guard is live |
| 15 rapid `POST /auth/login` | all `401`, no `429` | **the rate limits do not count** — section 8, and the fix needed a redeploy (made later the same day; the re-check is below) |

And the first-visit cost, which is a reviewer's first impression: 48s for the first page load, 2s once
warm, 28s for a route's own first hit, and 1s from the API when awake. That is `ADR-0011`'s accepted
trade, with the keep-alive ping that the ADR names as the mitigation still unbuilt.

Two items remained after that first verification, both outside this repository: a redeploy with the
corrected `NINJA_NUM_PROXIES`, and a sign-in through the live stack, which needs a browser.

**After the redeploy, 2026-10-12 (same day).** Re-checked from outside, and then re-checked again
when the first look turned out to have been early:

| Check | Result | The assertion |
| --- | --- | --- |
| `GET /healthz` | `200` | the service is up after the redeploy |
| `GET /api/v1/openapi.json` | advertises `/api/v1/cart` and its two siblings | the deploy carried `M3.1`'s code and not only `M2`'s — and, since the boot path runs `migrate`, the cart tables exist with it |
| `GET /cart` on Vercel | `404` at 22:20, `200` at 22:56 | **the check was early, not the deploy wrong** — see below |
| A cart driven through the live API | 16 of 17 assertions | `M3` works against Supabase: add, increment (one line, not two), update, `409` above stock, remove, and the removal persists |
| The `409` body | `Only 1 of Heia Ash Shelving Unit (Clay) in stock; 3 requested.` | `US-3.2`'s "clear message" names the product, the variant, the stock and the request |
| `POST /cart/items` with no token | `401` | the cart is behind the token in production, not only in tests |
| The product page | three `radio` inputs, prices 851.00 / 917.00 / 896.00 | the colour choice is live, and each option carries its own variant's price |
| `GET /cart` shape | `200`, title "Your cart — LYSHEIM", the `restoring` state | the route and its metadata are live; the signed-in states need a browser |

**The lesson from the `404`.** The frontend looked stale — `/cart` 404, the old product page — and it
was not: the Vercel build was still running when it was checked. Green in one system says nothing
about another system's queue, and a deployment is only verified once the deployment carrying it has
finished. Wait for the build to land, then look.

**The rate limit still does not count the visitor**, and the cause is now narrowed to a place to look
rather than a guess. Fifteen sequential `POST /auth/login` attempts from one client produced fifteen
`401`s and no `429` — the same symptom as before the redeploy, when 40 attempts produced one `429`.
That rules out both explanations visible from this repository: the container runs `uvicorn` with no
`--workers`, so the throttle's in-process cache is a single process and its counter is shared; and
`prod.py` defaults `NINJA_NUM_PROXIES` to 2. So the running instance is reading a different value
from its environment — the dashboard's own `NINJA_NUM_PROXIES`, which overrides `render.yaml` and the
code default alike.

> **Action on Render's dashboard:** set `NINJA_NUM_PROXIES` to `2`, or delete it so `prod.py`'s
> default applies, then redeploy. Expected afterwards: fifteen rapid attempts end in `429`s from the
> eleventh, and a forged `X-Forwarded-For` prefix does not open a bucket of its own.
>
> **Still open on 2026-10-13**, re-checked three times against the `M4` deploy. Fifteen rapid
> `POST /auth/login` with a wrong password produced fifteen `401`s and no `429`; then it was confirmed
> that the dashboard's `NINJA_NUM_PROXIES` **is** `2` and the service was redeployed, and a third check
> gave the same fifteen `401`s. The dashboard-override explanation is therefore dead — and with it the
> assumption that `2` is the right number.
>
> Ninja indexes the comma-split header as `addrs[-min(num_proxies, len(addrs))]`, so `2` counts the
> *second* entry from the right. For the limit to miss, that entry has to change between requests, which
> means it is infrastructure rather than the visitor: the chain carries more hops than the two
> Cloudflare-then-Render assumed here. MDN states the general rule — with *N* proxies the last *N-1*
> entries are internal — so the value is probably `3`, and almost certainly not `2`.
>
> **Do not reason the number out a third time; measure it.** Log the resolved ident (or the raw header)
> once from the running instance, read it in Render's logs, and set `NINJA_NUM_PROXIES` to the position
> the visitor actually occupies. This is the same lesson as §7.8: the deployed API gets measured, not
> reasoned about, because every test and every `docker compose up` passes while the wiring is wrong.

The correction itself is pinned by
`tests/test_accounts_api.py::test_the_counted_address_is_the_client_and_not_a_hop_in_front_of_it`;
what was never verified is the dashboard's value.

**After `M4.3` and `M4.4`, 2026-10-13.** The checkout path re-checked from outside, because it is the one
journey that writes stock, an order and a payment inside a single request, and a test that shares a
process with the code cannot show all three landing in Supabase:

| Check | Result | The assertion |
| --- | --- | --- |
| `GET /api/v1/openapi.json` | advertises `/orders`, `/payments/mock/confirm`, `/payments/mock/fail` | the deploy carried `M4.3`'s code — and, since boot runs `migrate`, the order and payment tables came with it |
| `POST /api/v1/orders`, no token | `401` | creating an order is behind the token in production, not only in tests |
| `POST /api/v1/payments/mock/confirm`, no token | `401` | so is settling one |
| A checkout driven through the live API | quote `106500`; order `LSH-DA8B2C1D` `pending`; total `108400` | cart → quote → order works against Supabase, and the chosen method's cost is carried into the total rather than recomputed |
| The same `Idempotency-Key` twice | `201`, then `200` with **one** number | `NFR-4` holds where the row to find is in Supabase rather than in a test transaction |
| `POST /payments/mock/confirm` | `order_status: paid`, `payment_status: succeeded` | the deployed `PAYMENT_PROVIDER=mock` selects the mock adapter |
| The same confirm again | `409` | nothing left to settle, and the second call did not move the order back |
| `GET /api/v1/orders` | `405` | only `POST` exists until `M4.6`; the contract, not a fault |

**What it does not cover.** `M4.4`'s email has no effect this vantage point can see: the deployed mailer
throws the message away (`dummy`, per `prod.py`), and the `immediate` task backend catches a task's
exception onto a `TaskResult` nobody reads instead of raising it. So the confirm above proves the
endpoint completed and cannot distinguish a rendered receipt from a failed one — a blind spot worth
closing with a `task_finished` receiver that logs failures.

The smoke left `smoke-m4@example.com`, its cart and the paid order `LSH-DA8B2C1D` in the demo database,
and one unit off `brisk-ash-dining-chair` variant 13; delete the account the way §7.5 describes.

## 8. Troubleshooting

> Accumulates as real problems occur (e.g. Postgres connection, port conflicts, cold-start
> latency, migration drift).

- **The rate limits stop counting in production, while passing every test.** `NINJA_NUM_PROXIES` was
  `1`, and at `1` Ninja's `get_ident` takes the *last* `X-Forwarded-For` entry — the address the
  nearest proxy appended. Render serves `.onrender.com` through Cloudflare, so that entry belongs to
  Cloudflare's edge rather than to the visitor, and it rotates between requests: forty rapid
  `POST /auth/login` attempts from one client produced **one** `429`, at attempt 23. The limit was
  counting neither the client nor a bucket anyone shares. It is `2` now (skip the balancer's entry,
  land on the client's); at `3` a forged header would become the key, so this has to match the chain
  rather than err upward. `base.py` carries the reasoning and
  `tests/test_accounts_api.py::test_the_counted_address_is_the_client_and_not_a_hop_in_front_of_it`
  pins both wrong directions. The symptom to recognise: a limit that is correct in every test and in
  `docker compose`, and never fires on the internet.
- **A Render deploy fails at start-up with `python manage.py migrate … : not found`.** A compound
  command in `render.yaml`'s `dockerCommand`. Render strips a leading `/bin/sh -c` from that field and
  runs the remainder through its own shell, so the quotes that a `&&` chain needs turn the entire
  command into one word that does not exist. Observed at `M2.7`, and reproduced without Render:

  ```bash
  docker run --rm alpine sh -c '"echo a && echo b"'   # sh: echo a && echo b: not found
  docker run --rm alpine sh -c 'echo a && echo b'     # prints both lines
  ```

  The field holds one token now (`/app/docker-entrypoint.sh`) and the compound command lives in the
  image, where it can be read and tested. The same trap applies to any `&&` chain in a platform field
  that parses its own shell — put it in a file.

- **`Backend CI` fails at "Set up job" with `unable to resolve action 'astral-sh/setup-uv@vN'`.**
  setup-uv stopped publishing floating major tags after `v7`; `v8`, `v9`, and `v10` do not
  exist as tags even though `v8.3.2`…`v10.3.0` do. Pin an exact release (currently `v10.3.0`)
  and check before changing it:
  `curl -s https://api.github.com/repos/astral-sh/setup-uv/tags`.
- **`basedpyright` cannot see reverse foreign-key accessors** such as `category.children` or
  `product.images`. django-stubs implements reverse relations in a *mypy* plugin, and pyright
  has no Django plugin, so the checker reports `reportAttributeAccessIssue` on attributes that
  are real at runtime. **The convention is to query explicitly** —
  `ProductImage.objects.filter(product=product)` rather than `product.images.all()`. Relation names
  as strings are also fine (`prefetch_related("images")`, `filter(images__isnull=False)`) and avoid
  N+1. Never `cast` a reverse accessor. See
  [`../decisions/ADR-0014-reverse-relations-under-basedpyright.md`](../decisions/ADR-0014-reverse-relations-under-basedpyright.md).
- **`basedpyright` also cannot see an implicit primary key (`id`) or foreign-key attnames**
  (`parent_id`, `product_id`). Same root cause as the bullet above: django-stubs generates them in
  its *mypy* plugin, and its own stub says other type checkers will not understand them. `pk` *is*
  declared, so `instance.pk` checks, but prefer passing field names as strings —
  `Product.objects.values("id", "parent_id")`, `filter(product_id__in=...)` — which works in every
  reader and keeps a page to a fixed number of queries. `catalog/api.py` is written this way.
- **A blanket `try`/`catch` around a Server Component `fetch` reports a false outage on every
  build.** Under Partial Prerendering a request-time `fetch` is aborted once the shell's prerender
  completes, and Next signals that by throwing — so a `catch` logs "the service could not be
  reached" for a request that was never meant to finish. Call `unstable_rethrow(error)` as the
  first line of the catch block. The docs list `fetch` with `cache: 'no-store'`, alongside
  `cookies`, `headers`, and `searchParams`, as APIs whose errors must be rethrown. Found at `M1.5`:
  `/products` logged six of these per build, and none after the fix, while a genuinely unreachable
  backend still logs and still renders the retry panel.
- **Running `pnpm build` while `pnpm dev` is running can break the dev server.** Both use `.next`,
  so a build overwrites the tree the dev server is serving from and it can stop responding —
  `curl` then fails with a connection error and nothing obvious is logged. Stop the dev server
  before building. This is easy to walk into when a verification pass builds repeatedly while a
  development server is open in another terminal.
- **`basedpyright` reports "Base classes for class `User` define variable `Meta` in incompatible
  way".** `django-stubs` declares a nested `Meta` on both `AbstractBaseUser` and `PermissionsMixin`
  and types the two nominally, so *every* custom user model built the documented way —
  `AbstractBaseUser` plus `PermissionsMixin` — is reported as an incompatible override, whether or
  not it declares a `Meta` of its own. Same root cause as `ADR-0014`: a stub cannot express
  something the framework genuinely allows. The two scoped `pyright: ignore` directives in
  `accounts/models.py` are the entire cost. Do not "fix" it by subclassing `AbstractUser`, which
  would add `first_name`, `last_name` and `date_joined` that `DATA-MODEL.md` section 2 does not
  specify.

## 9. Operators

> Added at `M5.2`, once the console existed (`M5.1`). `ADR-0007` chose Django admin for v1,
> `SCOPE.md` §8 D1 fixed its form, and `API.md` §9 fixed its path.

Numbered after §8 rather than slotted in before §7 because the sections around it are cited by number
from elsewhere — `ADR-0014` points at §8, the roadmap and the change log at §7.8 — and a runbook whose
numbers move is a runbook whose cross-references rot.

The console is at `/admin/`. Everything an operator does, they do there.

### 9.1 Making an operator

An operator is an account with `is_staff` (`DATA-MODEL.md` §2), which is the flag `ADR-0007` gates on.
A visitor is sent to the login page and a signed-in *customer* is refused; `is_staff` is the whole
difference.

```bash
cd backend
uv run python manage.py createsuperuser            # prompts for an email and a password
uv run python manage.py changepassword ops@example.com
```

`createsuperuser` sets `is_staff` **and** `is_superuser`. The two are not the same, and the gap is worth
knowing before it surprises you:

- `is_staff` gets the account *into* `/admin/`. It is what `AdminSite.has_permission` checks.
- `is_superuser` is what grants the *model permissions* the console then checks, per table and per
  action.

So an account with `is_staff` and nothing else reaches the console and is refused every list and every
action. That is Django working as designed, and it reads like a broken login; `createsuperuser` gives
the first operator both flags, which is why §9.1 leads with it.

For a second operator who should not hold the whole shop, keep `is_staff` and grant permissions on the
user's own page — *User permissions*, per app and per model (`catalog | product | Can change product`,
`orders | order | Can change order`, …). The console's order actions are declared with `change`
permission, so an operator without it can read an order and cannot move one.

Two commands, no sign-up page and no invitation flow. Deliberate: an account that can see every
customer's order should not be creatable from a form on the internet.

### 9.2 Signing in

`/admin/` in a browser, with that email and password. This session has nothing to do with the
storefront's — the console uses `M5.1a`'s cookie session, the storefront uses `ADR-0009`'s JWT pair —
so an operator who also shops has two independent sessions, and that is expected. Signing out of one
does not touch the other.

### 9.3 The catalog — `US-5.1`-`US-5.3`

- **Categories** and **Products** are lists with a filter and a search box; a slug fills itself in from
  the name.
- **A product's variants and images are on the product page**, below it, not a page away.
- **Money is in cents**, because that is how it is stored (`DATA-MODEL.md` §5): `12900` is `$129.00`. A
  variant's `price_cents` is what a customer is charged; `Product.base_price_cents` is the product's
  own price field.
- **Stock is edited straight from the variant list**, because a season's worth of SKUs is one page of
  edits rather than one SKU at a time. The **stock** column reads *Out of stock*, *Low* or *In stock*
  in words (`NFR-2`), and the **stock** filter beside it selects the low and the empty ones.
- **"Low" means five or fewer** (`catalog/admin.py`, `LOW_STOCK_THRESHOLD`). It is a display choice and
  not a rule: nothing server-side refuses a sale at that number, and the only rule on stock is that it
  cannot go below zero.
- **Image credits** are their own table. An image's credit is optional on the model, so this is where
  the attribution an image *does* carry is kept, and `US-6.1`'s page renders from it (`M6`).

### 9.4 Orders — `US-5.4`, `US-5.5`

The order list filters by status and by date, and searches by number, email or recipient. Open one and
it is **a receipt, not a form**: every field is read-only, the lines are the lines as they were bought,
and the timeline at the foot is the whole history — who moved it, when, and from what to what.

It moves by **action**. Select orders on the list and choose one from the dropdown:

| Action | Moves an order from | to |
|---|---|---|
| Mark as paid | `pending` | `paid` |
| Mark as shipped | `paid` | `shipped` |
| Mark as delivered | `shipped` | `delivered` |
| Cancel and return to stock | anywhere but `cancelled` | `cancelled` |

Those are `DATA-MODEL.md` §3's transitions and nothing else. The console cannot skip a step: choosing
*Mark as shipped* for a `pending` order leaves it where it was, says so, and writes no event. Every move
that does happen writes one, under the operator's name.

**Cancel is the one move that touches the catalog.** Checkout reserved the stock (`ADR-0017`), so
cancelling puts it back on the shelf — which is why the action says "and return to stock", and why it
goes through the same function the API would use rather than assigning the status. An order that has
shipped, or been delivered, can still be cancelled: a return is a cancellation, and the timeline keeps
the whole story.

**A selection is not all or nothing.** Tick two orders where one has already moved and the one that can
move does; the report names both — the orders moved and the ones left alone.

### 9.5 What the console will not do

- **It will not save an order.** There is no Save button, because there is no editable field; the row
  offers Close instead, which is the page saying that movements are the actions.
- **It will not add or delete an order.** An order is what checkout writes, and a receipt is not a
  thing to remove — cancelling is how an order is undone, and cancelling is recorded. Both URLs answer
  `403` rather than the button merely being hidden.
- **It will not accept a status you type.** There is no input for it anywhere, which is what keeps
  `ALLOWED_TRANSITIONS` a rule rather than a suggestion (`M5.1b`).
