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

## 7. Deployment (M7)

> Filled in at M7 — Render, Vercel, Supabase steps, environment variables, and the production
> smoke journey. See [`../decisions/ADR-0011-deployment-stack.md`](../decisions/ADR-0011-deployment-stack.md).

## 8. Troubleshooting

> Accumulates as real problems occur (e.g. Postgres connection, port conflicts, cold-start
> latency, migration drift).
