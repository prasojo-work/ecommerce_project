# LYSHEIM — frontend

Next.js (App Router, React Server Components) + TypeScript. See the project docs in
[`../docs`](../docs), especially [`../docs/02-product/UX.md`](../docs/02-product/UX.md).

## Conventions

- **Tailwind CSS** does the styling (`ADR-0013`). The design tokens from `UX.md` §2 are declared
  in the `@theme` block in `src/app/globals.css`; use the utilities it generates (`bg-canvas`,
  `text-ink`, `max-w-measure`) rather than raw hex values or inline styles.
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
