import Link from "next/link";
import { Suspense } from "react";

import { fetchProducts } from "@/api/client";
import { EmptyState } from "@/components/empty-state";
import { ProductCardSkeleton } from "@/components/product-card-skeleton";
import { GRID_COLUMNS, ProductGrid } from "@/components/product-grid";
import { RetryPanel } from "@/components/retry-panel";
import { FEATURED_COUNT, selectFeatured } from "@/lib/featured";

/**
 * The home page (`US-1.5`): a hero, a featured row, and one saturated closing band.
 *
 * **The composition changed at `M7.4`, and the reason is in `UX-DIRECTION.md` section 1.** It was a
 * text hero followed by an even grid — every element the same weight, no focal point, one volume
 * level. It is now the loud/quiet field that document asks for: one display heading at `text-7xl`,
 * one terracotta band, and a featured row that is deliberately quieter than either.
 *
 * The hero is still text and nothing else, and that is still the right call for a different reason
 * than before: `US-1.5` wants a fast LCP, and the heading ships inside the static shell so the
 * largest paint is a glyph rather than a download. `M7.4` makes that heading *loud* instead of
 * replacing it with a photograph — the direction document's section 5 explains why "Room, not grid"
 * waits for an image budget.
 *
 * The featured grid waits behind a `<Suspense>` boundary, which is both its loading state and, with
 * `cacheComponents: true`, the requirement for reading an uncached endpoint. The heading stays
 * outside that boundary because it belongs to the shell and reserves the section before the products
 * arrive.
 *
 * The page declares no metadata of its own: it inherits the root layout's brand title and house
 * line, which is what a home page should be announcing anyway (`NFR-6`).
 */
export default function HomePage() {
  return (
    <main>
      <div className="mx-auto max-w-6xl px-6 pb-16 pt-20">
        <p className="text-xs uppercase tracking-[0.14em] text-muted">LYSHEIM — household goods</p>
        <h1 className="mt-4 max-w-3xl text-6xl text-ink sm:text-7xl">
          Furniture for the long stay.
        </h1>
        <p className="mt-6 max-w-measure text-lg text-muted">
          Every piece lists its material, its finish and whether it is in stock — before you fill a
          cart.
        </p>
        <Link
          href="/products"
          className="mt-8 inline-flex min-h-11 items-center rounded-lg bg-primary px-6 text-primary-ink"
        >
          Browse the catalog
        </Link>
      </div>

      <section aria-labelledby="featured-heading" className="mx-auto max-w-6xl px-6 pb-20">
        <div className="border-t border-border pt-6">
          <p className="text-xs uppercase tracking-[0.14em] text-muted">Featured</p>
          <h2 id="featured-heading" className="mt-2 text-3xl text-ink">
            Statement pieces
          </h2>
          <p className="mt-3 max-w-measure text-muted">
            The highest-priced piece from each part of the collection.
          </p>
        </div>
        <Suspense fallback={<FeaturedSkeleton />}>
          <FeaturedProducts />
        </Suspense>
      </section>

      {/* The one saturated surface on the route (`UX-DIRECTION.md` section 3). It carries the closing
          action, so the page does not end on a grey paragraph and a text link. */}
      <section aria-labelledby="closing-heading" className="bg-accent text-accent-ink">
        <div className="mx-auto flex max-w-6xl flex-col items-start gap-4 px-6 py-14 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h2 id="closing-heading" className="text-3xl">
              The rest of the collection
            </h2>
            <p className="mt-2 max-w-measure">
              Sizes, materials and finishes on every line — the questions you would otherwise have
              to email about.
            </p>
          </div>
          <Link
            href="/products"
            className="inline-flex min-h-11 shrink-0 items-center rounded-lg bg-surface px-6 text-ink"
          >
            See every piece
          </Link>
        </div>
      </section>
    </main>
  );
}

/**
 * The featured row.
 *
 * The whole priciest page of the catalog is the pool, not just the first few: `selectFeatured` takes
 * one piece per category from the top of it, so the wider the pool the truer "one from each part of
 * the collection" is. Fetching exactly four would usually return four products from two categories.
 */
async function FeaturedProducts() {
  const result = await fetchProducts({ page: 1, sort: "-price" });

  if (!result.ok) {
    return <RetryPanel message={result.message} />;
  }

  const featured = selectFeatured(result.data.items);

  if (featured.length === 0) {
    // An empty catalog. This is the copy `UX.md` section 5 already fixes for the catalog grid, so
    // the two screens agree rather than saying the same thing two ways.
    return <EmptyState title="No products yet" />;
  }

  return (
    <div className="mt-10">
      <ProductGrid products={featured} />
    </div>
  );
}

/** The featured row's loading state: `FEATURED_COUNT` reserved tiles, the same shape as the grid. */
function FeaturedSkeleton() {
  return (
    <div role="status" className="mt-10">
      <span className="sr-only">Loading featured pieces…</span>
      <div aria-hidden="true" className={GRID_COLUMNS}>
        {Array.from({ length: FEATURED_COUNT }, (_, index) => (
          <ProductCardSkeleton key={index} />
        ))}
      </div>
    </div>
  );
}
