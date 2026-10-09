# TODO — Frontend Engineering (raw working file)

> Raw output of the `senior_frontend_engineering` hat for LYSHEIM. Curated sources:
> [`../02-product/UX.md`](../02-product/UX.md) and
> [`../03-architecture/ARCHITECTURE.md`](../03-architecture/ARCHITECTURE.md).

## Context

- Stack: Next.js (App Router, RSC), TypeScript strict, `pnpm`, ESLint + Prettier, Vitest.
- Scope: storefront, accounts, cart, checkout, orders. Operator console is Django admin
  (`ADR-0007`).

## Design Items

- [ ] **FE-1.1 [App structure]** — route groups `(shop) (auth) account cart checkout orders`;
  RSC by default, client components only where interactive.
- [ ] **FE-1.2 [Design system]** — tokens from `UX.md` §2 → `globals.css`; build the 30
  components (`UX.md` §6).
- [ ] **FE-1.3 [API client]** — types generated from the OpenAPI schema; typed fetch wrapper.
- [ ] **FE-1.4 [Session]** — in-memory access token + silent refresh; httpOnly refresh cookie
  (`ADR-0009`).
- [ ] **FE-1.5 [State]** — server state via RSC/`fetch`; minimal client state for cart UI.
- [ ] **FE-1.6 [Performance]** — image optimization, route-level code splitting, LCP budget
  (NFR-1).
- [ ] **FE-1.7 [Accessibility]** — WCAG 2.1 AA per `UX.md` §7; keyboard + axe pass.
- [ ] **FE-1.8 [Testing/tooling]** — Vitest unit tests; `tsc --noEmit`; ESLint; Prettier;
  optional Playwright E2E for the happy path.

## Quality Gates

- [ ] `tsc --noEmit` clean. · [ ] `eslint` clean. · [ ] `pnpm build` succeeds.
- [ ] `vitest` green; axe clean on key routes.

## Commands

- Dev: `pnpm dev` (port 3000) · Checks: `pnpm typecheck && pnpm lint && pnpm test && pnpm build`
