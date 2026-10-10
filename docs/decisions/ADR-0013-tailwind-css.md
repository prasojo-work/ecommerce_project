# ADR-0013 — Tailwind CSS for frontend styling

- **Status:** Accepted
- **Date:** 2026-10-10
- **Deciders:** Founder
- **Consulted hats:** senior_frontend, senior_ui-ux

## Context

`M0.2` shipped the frontend with no styling framework: design tokens as `--lys-*` custom
properties in `globals.css`, components styled with CSS Modules. The `v0.1.6` changelog entry
records that decision together with the condition attached to it — *"adopting a CSS framework is
deferred to its own ADR before the catalog UI is built at `M1.5`"*.

The catalog UI is now one milestone away (`M1.5` listing, `M1.6` product detail, `M1.8` home) and
is the largest surface this project will build. The question is therefore live now, not at
`M1.5`: build that surface in CSS Modules, or adopt a utility framework first.

The cost of changing this later is not flat. Today the entire styled surface is one placeholder
page and one CSS module. After `M1.5`–`M1.8` it is the whole storefront.

## Options considered

1. **Keep CSS Modules.** Pros: zero dependencies; the tokens and base layer already work;
   nothing to migrate; colocated styles read plainly. Cons: every component needs a parallel
   `.module.css`; spacing, colour, and type decisions are re-made by hand in each file; no shared
   constraint, so drift is caught only by review; responsive and state variants are hand-written.
2. **Adopt Tailwind CSS v4.** Pros: the token set *becomes* the design system — utilities are
   generated from the same values in `UX.md` §2, so a raw hex value has no natural place to hide;
   variants (`hover:`, `focus-visible:`, `md:`) are built in; no per-component CSS file; v4 is
   CSS-first (`@theme` in CSS, no JS config), so it does not create a second source of truth for
   design values. Cons: a class-heavy JSX surface; a build-tooling dependency (a PostCSS plugin,
   which Next.js already drives); the existing page must be migrated.
3. **Adopt CSS-in-JS (vanilla-extract, Panda).** Pros: typed tokens, colocated. Cons: more
   machinery than this project needs, one more build integration to keep working, and RSC
   support is less settled. Rejected as disproportionate for a solo portfolio build.

## Decision

Adopt **Tailwind CSS v4** (option 2), wired through `@tailwindcss/postcss`.

- The values from `UX.md` §2 move into a `@theme` block in `src/app/globals.css` so Tailwind
  generates `bg-canvas`, `text-ink`, `max-w-measure` and the rest from the existing values.
  `UX.md` §2 stays the source of truth; this ADR changes where the values are *declared*, not
  what they are.
- A small `@layer base` keeps the cross-cutting rules that must hold on every route and would
  otherwise have to be repeated everywhere: the `:focus-visible` ring (`UX.md` §7), heading
  line-height and `text-wrap: balance`, the anchor colour, and the body background and text
  colours.
- Components use utilities. CSS Modules are retired and `src/app/page.module.css` is deleted.
- Spacing and radii get no custom theme entries: the project's 4px scale and its 8px/16px radii
  are exactly Tailwind's defaults, so `p-4` and `rounded-lg` already mean the token values.

## Consequences

- The design system is enforced by the toolchain rather than by review — a colour outside the
  palette shows up in a diff as an obvious arbitrary value.
- `M1.5`–`M1.9` are written in Tailwind from their first commit, so no component is styled twice.
- The frontend gains a styling dependency to keep current, and class strings in JSX are denser
  than CSS Module selectors.
- Prettier already formats CSS and JSX, so formatting stays deterministic.
- The `v0.1.6` decision is reversed. That decision was recorded in the changelog rather than as
  an ADR, so there is no `Superseded` status to set on another record; this ADR supersedes it in
  practice.

## Reversibility

**Moderate.** Reverting means restoring the `--lys-*` custom properties and CSS Modules and
re-styling the surface. Cheap today — one page — and increasingly expensive after each UI
increment, which is exactly why the decision was taken now rather than at `M1.5`.

## References

- `docs/02-product/UX.md` §2 (design tokens) and §7 (accessibility)
- `docs/CHANGE-LOG.md` — `v0.1.6`, the decision this supersedes
- `docs/04-delivery/ROADMAP.md` — `M0.2`, `M1.5`–`M1.9`
- Tailwind CSS v4, [Installing with PostCSS](https://tailwindcss.com/docs/installation/using-postcss)
