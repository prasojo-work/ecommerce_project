import Link from "next/link";
import { Suspense } from "react";

import { fetchProducts } from "@/api/client";
import { EmptyState } from "@/components/empty-state";
import { ProductCardSkeleton } from "@/components/product-card-skeleton";
import { GRID_COLUMNS, ProductGrid } from "@/components/product-grid";
import { RetryPanel } from "@/components/retry-panel";
import { FEATURED_COUNT, selectFeatured } from "@/lib/featured";

/**
 * The home page (`US-1.5`): a hero and a featured grid, with the primary call to action into the
 * catalog.
 *
 * The hero is text and nothing else. `US-1.5` asks for a "fast LCP", and text keeps the largest
 * paint on a heading that ships inside the static shell. A photograph would need an LCP decision of
 * its own, a pick from the licence-clean set, and — because `ADR-0012` puts attribution on
 * `/pages/credits` rather than inline — a felt absence at exactly the focal point of the page. It
 * is the composition the milestone does not need to buy yet.
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
    <main className="mx-auto max-w-6xl px-6 py-16">
      <div className="flex max-w-2xl flex-col items-start gap-4">
        <h1 className="text-5xl tracking-tight">LYSHEIM</h1>
        <p className="text-lg text-muted">Warm, considered furniture for the long stay.</p>
        <Link
          href="/products"
          className="mt-2 inline-flex min-h-11 items-center rounded-lg bg-primary px-6 text-primary-ink"
        >
          Browse the catalog
        </Link>
      </div>

      <section aria-labelledby="featured-heading" className="mt-20">
        <h2 id="featured-heading" className="text-2xl">
          Statement pieces
        </h2>
        <p className="mt-2 max-w-measure text-muted">
          The highest-priced piece from each part of the collection.
        </p>
        <Suspense fallback={<FeaturedSkeleton />}>
          <FeaturedProducts />
        </Suspense>
        <Link
          href="/products"
          className="mt-8 inline-flex min-h-11 items-center text-primary underline-offset-4 hover:text-ink hover:underline"
        >
          See the full catalog
        </Link>
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
    <div className="mt-8">
      <ProductGrid products={featured} />
    </div>
  );
}

/** The featured row's loading state: `FEATURED_COUNT` reserved tiles, the same shape as the grid. */
function FeaturedSkeleton() {
  return (
    <div role="status" className="mt-8">
      <span className="sr-only">Loading featured pieces…</span>
      <div aria-hidden="true" className={GRID_COLUMNS}>
        {Array.from({ length: FEATURED_COUNT }, (_, index) => (
          <ProductCardSkeleton key={index} />
        ))}
      </div>
    </div>
  );
}
