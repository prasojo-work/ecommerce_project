# ADR-0013: Catalog caching — one read cache in the API, and why not in Next.js

- **Status:** Accepted
- **Date:** 2026-10-07
- **Deciders:** Founder
- **Related:** `ADR-0005`, `ADR-0012`, `M1`, `SECURITY-REVIEW.md`

## Context

M6's performance pass had to settle an open question: M1's exit criterion says
"catalog reads are cached", and `ARCHITECTURE.md` §9 targets "API p95 < 400 ms
(catalog, **cached**)" — but there was no cache anywhere. `config/settings.py`
defined no `CACHES`, and `catalog/` referenced no cache at all. The claim was
aspirational, and the roadmap recorded it as a gap needing a decision.

Four facts shaped the decision:

1. **The shop route cannot be cached in Next.js.** `/products` reads
   `searchParams` (filters, sort, page), which makes the route dynamic, and the
   page also sets `dynamic = "force-dynamic"` — which, per the framework docs, is
   equivalent to forcing every `fetch` in the route to `no-store`. So Next's data
   cache cannot serve the busiest catalog route, no matter what the `fetch` call
   asks for.
2. **The product detail route already caches its data.** `fetchProduct` uses
   `next: { revalidate: 60 }`, so the detail page's API call is served from Next's
   data cache. Only the listing and categories fetched with `no-store`. (The route
   itself still renders on demand — `next build` reports `/products/[slug]` as
   dynamic — so it is the cached *data* that saves the round trip, not a stored
   HTML response.)
3. **The API is not currently slow.** Measured locally against the seeded
   catalogue, the listing endpoint answered in **36–46 ms** — roughly 10× inside
   the 400 ms target. Caching it is not a fix for a present bottleneck.
4. **The deployment target is where that stops being true.** `ADR-0005` puts the
   API on a free tier that sleeps, and the database on a free tier that pauses.
   Every listing render is a dynamic render, so it hits the API and therefore the
   database — the slowest, most fragile hop — on every request, for every
   visitor, with no cache between them.

## Options considered

1. **Rely on Next.js caching alone.** Free, but fact 1 makes it impossible for the
   listing route. It would leave the documented criterion unmet.
2. **Cache catalog reads in the API, in-process, invalidated on write** — chosen.
   Removes the database round trip from every dynamic render, works for any
   client, and needs no new infrastructure.
3. **Cache in a shared backend (Redis/Upstash) from the start.** Global and
   restart-proof, but adds a paid-ish dependency and a second thing to operate,
   for a project currently running one API worker.
4. **Descope the criterion instead** — delete the "cached" claim, since the API
   already beats the latency target by 10×. Honest, and defensible today; but it
   optimises for the local measurement rather than the deployment target, and
   leaves the free-tier behaviour (fact 4) unaddressed.

## Decision

Take **option 2**, with the frontend made explicit about what is cacheable.

- **`catalog/cache.py`** holds the whole mechanism: a `cached(key, build)` helper
  and an `invalidate_catalog_cache()`. Every entry sits behind a **version token**
  that a write bumps. Old entries are never looked up again and expire unread, so
  invalidation is O(1) and backend-agnostic — it never needs `delete_pattern()`,
  which not every cache backend implements.
- **`catalog/signals.py`** retires the generation on every `post_save`/`post_delete`
  for `Category`, `Product`, `ProductVariant` and `ProductImage`. This covers
  checkout's stock decrements, because those go through
  `variant.save(update_fields=[...])`, which fires `post_save`.
- **The TTL (300 s) is a backstop, not the freshness mechanism.** It bounds the
  damage if a write path ever bypasses ORM signals — a bulk `QuerySet.update()`,
  say — rather than governing when edits appear.
- **`CACHES` is settings-driven** (`CACHE_URL`), defaulting to an in-process
  backend. The same setting backs the API's rate limits, so moving to a shared
  cache later fixes both per-process limitations in one change.
- **The frontend states its intent.** Public catalog `fetch` calls now use
  `next: { revalidate: 60, tags: ["catalog"] }` instead of `cache: "no-store"`.
  This is a correctness-of-intent fix rather than a measurable win on today's
  routes (fact 1), and it means any future static consumer of the catalogue is
  cached by default. Per-user reads (`requestJson`: cart, orders, auth) pass no
  cache option and therefore stay uncached, which is the behaviour we want — the
  change is deliberately confined to the public catalog reads.

## Consequences

- **Positive:** the database is out of the hot path for catalog reads. Measured on
  the seeded catalogue: the listing went from ~37 ms to **~1.8 ms** and the detail
  from ~26 ms to **~1.7 ms** on a warm cache, with `0` SQL queries asserted by
  test on a repeat read. Writes are visible on the next request, not after a TTL.
- **Negative / costs:** the cache is **per process** — it does not survive a
  restart (so it does not help a sleeping free-tier instance wake up) and it
  multiplies rather than shares across workers. There are now **two caches with
  independent expiries**: the API invalidates instantly, but the Next.js detail
  page revalidates on its own 60 s clock, so a catalogue edit can take up to that
  long to surface there. And an unknown slug is cached as a 404 for the TTL.
- **Follow-ups:** move to a shared cache when more than one worker runs (the same
  trigger as `ADR-0012`'s throttles). A Django→Next purge hook would collapse the
  second layer's window; without one, the 60 s revalidate is the effective
  worst-case staleness for a product page and should be documented as such.

## Reversibility

**Two-way door.** The mechanism is one helper and one signal module; deleting the
`cached(...)` wrappers in `catalog/api.py` restores the previous behaviour, and
the TTL/`CACHE_URL` are settings. No schema change, no new dependency.
