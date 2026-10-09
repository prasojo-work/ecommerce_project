# LYSHEIM — backend

Django 6 + Django Ninja API. See the project docs in [`../docs`](../docs), especially
[`../docs/03-architecture/ARCHITECTURE.md`](../docs/03-architecture/ARCHITECTURE.md).

## Conventions

- **Async** is used for I/O-bound handlers; background work uses Django 6's Tasks framework
  (see `ADR-0006`). Prefer synchronous code where async adds nothing.
- **Configuration** comes from the environment (`django-environ`); never hard-code secrets.

## Quick start

```bash
uv sync
cp .env.example .env
uv run python manage.py migrate
uv run uvicorn config.asgi:application --reload
```

Quality gates:

```bash
uv run ruff check . && uv run ruff format --check .
uv run basedpyright
uv run pytest
```
