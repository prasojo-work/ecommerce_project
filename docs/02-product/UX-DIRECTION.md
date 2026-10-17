# UI/UX Direction — LYSHEIM "The Spec Sheet"

> Consulted hat: **Senior UI/UX Designer**. Owner: Founder.
> **Status:** adopted 2026-10-16, increment `M7.4`. This document fixes the *visual grammar* of the
> storefront. It does not replace [`UX.md`](UX.md): that file keeps the information architecture,
> the user flows and the states matrix, and this one decides what those pages *look like* and what
> makes them persuasive. Where the two disagree, this document wins on appearance and `UX.md` wins on
> behaviour.

## 1. Why this document exists

The storefront shipped complete and correct, and the founder's review of it was one sentence: *"the
current UI/UX feels boring."* That is a real defect report, but it is not yet an actionable one — so
the first job here is to make it specific, and the second is to fix the causes rather than the
feeling.

`UX.md` §2 already asked for the right things: "light, warm, and homely … calm and editorial, not
discount-retail. Generous whitespace, a warm neutral canvas, one confident accent, and large product
imagery." The implementation obeyed every clause and produced a page that is quiet, even, and says
very little. That is the trap in the brief: **calm is achieved by removing contrast, and contrast is
what makes a page feel designed.** Calm without tension is beige.

### The diagnosis, with evidence

| # | Cause | Where it shows |
| --- | --- | --- |
| 1 | **The focal point is empty.** The hero is text and nothing else. | `app/page.tsx` — the comment explains the LCP trade-off that bought a text hero. Right for `M1`; wrong for a furniture store's first screen. |
| 2 | **No type-scale contrast.** Largest step is `3rem`; a page's biggest element is ~38px against 14–16px body. One volume level. | `globals.css` `--text-5xl: 3rem` |
| 3 | **One rhythm, everywhere.** `max-w-6xl px-6 py-16`, `gap-4`, `mt-20` repeated. No tight, no generous, no tempo. | `app/page.tsx`, `product-grid.tsx` |
| 4 | **Uniform card chrome.** Every product the same `rounded-2xl` rectangle at `4:3`, in an even grid. Twelve equal rectangles. | `components/product-card.tsx` |
| 5 | **The accent is italicised, not shouted.** Terracotta "sparingly", green only on buttons → a grey-beige page. | `globals.css`, `UX.md` §2 colour rule |
| 6 | **No product truth in the tile.** Name and price only. The buying question — *will it fit, is it in stock* — is answered later. | `product-card.tsx` renders `name` + `price`; `material`, `color` and `in_stock` are already in the payload and unused |
| 7 | **No way into the catalog from the header.** The nav is account, cart, orders. | `components/site-header.tsx` |

Cause 6 is the important one. A quiet page that also withholds information is boring twice over, and
no amount of decoration fixes the second half.

## 2. The thesis

> **LYSHEIM is a catalog you can furnish a room from.** Every screen carries one loud element against
> a quiet field, and every product tells you the price, the material, the size and whether it is in
> stock — before it asks you for anything.

The second clause is as load-bearing as the first. Decoration alone would fix "dull"; information is
what fixes "empty". This is also why the concept is called **The Spec Sheet**: the identity is the
*label*, not the lifestyle photograph.

## 3. What the concept is

Household goods and furniture are bought by people who are about to measure a wall. `STRATEGY.md`
positions LYSHEIM as IKEA-inspired; IKEA's actual design genius is not beige minimalism, it is that
everything is labelled — dimensions, material, care, price, stock, whether it fits in the car. That
is a *visual* idea as much as an information one, and it is the one this storefront can execute
honestly with the photography it has.

**The motif: the spec line.** A short, monospaced-numeral line under every product:
`Oak · Natural · In stock`. It appears on the tile, in full on the detail page as a table, and in the
cart as a receipt line. It is the thing a visitor recognises the shop by.

**Typography carries the page.** The largest element on any route is a display serif at 56–72px
(`Fraunces`, one weight); the smallest is a 12px spec label. That 5–6× ratio is the loud/quiet field
the current build is missing. Prices and dimensions use tabular numerals so columns line up the way a
catalog's do.

**Colour appears in blocks, never as tints.** The warm canvas (`#FAF7F2`) stays. The terracotta
(`#B4552E`) becomes exactly one full-width band per page — the delivery promise — and the brand green
stays where it is, on actions. Nothing pastel, nothing gradient.

**Structure is rules and space, not cards.** Hairline rules (`--color-border`) separate sections and
sit above a tile's meta block. Radii shrink to the image frame only. A catalog page has rules,
not shadows.

**Imagery is framed, not cropped.** The frame becomes square (`1:1`), images stay `object-contain`.
`ADR-0012` forbids cropping images whose licence is `BY-ND` and the UI cannot branch on licence, so
nothing is cropped anywhere — the frame changes and the image is never cut.

**Density varies on purpose.** A loud band is tight and full-bleed; the featured row is airy; a spec
table is dense. The page has tempo instead of one even beat.

## 4. Three rules anyone can hold the UI to

1. **One loud thing per screen.** If two elements compete for the eye, delete one. (Measurable: one
   element at ≥ `3rem` per route, and it is a heading or a price.)
2. **No product tile without a spec line.** Name, price, and at least one of material/colour plus
   availability. A tile showing only name and price is incomplete.
3. **Colour appears in blocks, not tints.** A terracotta band is a decision; terracotta body text is
   decoration.

Two supporting constraints, which are gates rather than taste:

- **`NFR-2`** — never encode state by colour alone; the spec line's availability is text, not a dot.
  All new pairs are checked at ≥ 4.5:1 (muted `#57534E` on canvas `#FAF7F2` is ≈ 7:1).
- **`NFR-1`** — the display serif is a single weight, `display: swap`, and the hero heading remains
  the LCP element rather than becoming an image. See §7 for the risk and the back-out.

## 5. Alternatives considered, and what happened to them

**"Room, not grid"** — sell the room: full-bleed interiors, shop-the-room, categories named as rooms.
The highest ceiling and the lowest floor. It inherits exactly the constraint that made the text hero
the right `M1` call: keyword-matched stock imagery the project does not control, plus `ADR-0012`'s
attribution and an LCP decision of its own. **Deferred**, not rejected — it is the concept to revisit
when there is an image budget.

**"Warm editorial, turned up"** — keep the palette, add the type contrast and rhythm `UX.md` asked
for. Cheap and safe, and it was adopted *as the visual grammar* (serif display, loud/quiet rhythm,
rules) while being rejected *as the concept*, because it fixes "dull" and leaves "says little"
untouched.

## 6. What this changes, in order

1. **Tokens** (`app/globals.css`): a display font variable, four new large steps (`6xl`–`8xl`), a
   spec-label size/tracking pair, tabular numerals, and a named rule colour.
2. **Type system** (`app/layout.tsx`): load `Fraunces` (600) as `--font-display`.
3. **Product tile** (`components/product-card.tsx`): square frame, rule above the meta block, spec
   line, price promoted to display size with tabular numerals.
4. **Home** (`app/page.tsx`): display hero, one terracotta delivery band, section headers as rules
   with a spec label.
5. **Product detail** (`app/products/[slug]/page.tsx`): the existing `<dl>` becomes a two-column spec
   table with rules and tabular numerals; price promoted.
6. **Header** (`components/site-header.tsx`): a `Shop` link into the catalog, which the nav has never
   had.

## 7. Risks, and how they are paid for

- **LCP (`NFR-1`, 2.5 s throttled mobile).** A second web font is bytes on the critical path, and the
  hero heading is the LCP element. Mitigation: one weight only, `display: swap`, font subset `latin`.
  If `e2e/perf.spec.ts` regresses past budget, the back-out is to drop `Fraunces` and keep the scale
  in `Inter` at `-0.03em` tracking — the loud/quiet ratio survives, the warmth does not.
- **A spec line with empty data.** `material` and `color` are `blank=True` in the model. The seeder
  always generates both (`catalog/seeders.py`), but the UI must not render ` · · ` for a product that
  has neither: the line is assembled from the parts that exist and disappears entirely when none do.
- **Axe (`NFR-2`).** New text on new surfaces, so contrast and heading order are re-audited on all
  eleven routes in `e2e/a11y.spec.ts`, not just the changed ones.
- **Screenshots.** The images in the README are captured from a real journey; they are re-captured
  with this increment so the published pictures are of the published UI.

## 8. What this explicitly does not do

- **No new product capability.** No reviews, wishlist, promo codes, search changes or checkout
  changes. Those are separate increments with their own arguments.
- **No schema or API change.** Every field the spec line needs — `material`, `color`, `in_stock`,
  `width_cm`, `height_cm`, `depth_cm` — already exists and is already in the response.
- **No motion system yet.** Motion is the next increment's business; a page that moves before it has
  hierarchy is noise on top of noise.
- **No dark mode.** It is a design system of its own and there is no request for it.

## 9. How this document is revised

Adopted by `M7.4`. Revised when a route cannot meet §4's rules without breaking `NFR-1` or `NFR-2`,
or when the imagery situation changes enough to make "Room, not grid" affordable. Every revision is
recorded in [`../CHANGE-LOG.md`](../CHANGE-LOG.md), like any other decision here.
