# LYSHEIM — frontend

Next.js (App Router, React Server Components) + TypeScript. See the project docs in
[`../docs`](../docs), especially [`../docs/02-product/UX.md`](../docs/02-product/UX.md).

## Conventions

- **Design tokens** live in `src/app/globals.css` and are the single source of truth from
  `UX.md` §2. Components use the `--lys-*` variables, never raw hex values.
- **Server components by default.** Add `"use client"` only where interactivity requires it.
- **Configuration** comes from the environment; only `NEXT_PUBLIC_*` values reach the browser.

## Quick start

```bash
pnpm install
cp .env.example .env.local
pnpm dev
```

The app runs at <http://localhost:3000> and expects the API at
<http://localhost:8000> (see `NEXT_PUBLIC_API_BASE_URL`).

Quality gates:

```bash
pnpm typecheck
pnpm lint
pnpm format:check
pnpm test
pnpm build
```
