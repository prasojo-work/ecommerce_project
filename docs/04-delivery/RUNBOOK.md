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

> Filled in at M0.

```
# (M0) compose up — API + web + Postgres
docker compose up
```

## 3. Backend

```
# (M0) install
uv sync
# (M0) run
uv run uvicorn config.asgi:application --reload
# (M0) quality gates
uv run ruff check . && uv run ruff format --check . && uv run basedpyright && uv run pytest
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

## 7. Deployment (M7)

> Filled in at M7 — Render, Vercel, Supabase steps, environment variables, and the production
> smoke journey. See [`../decisions/ADR-0011-deployment-stack.md`](../decisions/ADR-0011-deployment-stack.md).

## 8. Troubleshooting

> Accumulates as real problems occur (e.g. Postgres connection, port conflicts, cold-start
> latency, migration drift).

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
