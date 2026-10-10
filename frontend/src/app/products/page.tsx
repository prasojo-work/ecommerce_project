import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";

import { fetchCategories, fetchProducts } from "@/api/client";
import { CatalogFilters } from "@/components/catalog-filters";
import { EmptyState } from "@/components/empty-state";
import { Pagination } from "@/components/pagination";
import { ProductGrid } from "@/components/product-grid";
import { ProductGridSkeleton } from "@/components/product-grid-skeleton";
import { RetryPanel } from "@/components/retry-panel";
import { isFiltered, parseCatalogQuery } from "@/lib/catalog-query";
import { pageCount } from "@/lib/pagination";

export const metadata: Metadata = {
  title: "Catalog — LYSHEIM",
  description: "Every piece in the LYSHEIM catalog.",
};

/**
 * The catalog listing page (`UX.md` section 5: search, filter, sort, pagination).
 *
 * The heading renders immediately and everything that depends on data sits behind one `<Suspense>`
 * boundary. That boundary is doing double duty, as on the rest of the catalogue: it is the loading
 * state, and with `cacheComponents: true` it is also required, because the uncached reads and the
 * `searchParams` read below cannot be resolved while the static shell is being prerendered.
 *
 * All listing state lives in the URL and none of it in component state, which is what `US-1.4`
 * means by "the URL reflects the filter state": a filtered, sorted, page-three view is a link
 * somebody can send, and the back button walks back through what the reader actually did.
 */
export default function CatalogPage(props: PageProps<"/products">) {
  return (
    <main className="mx-auto max-w-6xl px-6 py-16">
      <h1 className="text-4xl">Catalog</h1>
      <Suspense fallback={<ProductGridSkeleton />}>
        <CatalogResults searchParams={props.searchParams} />
      </Suspense>
    </main>
  );
}

async function CatalogResults({ searchParams }: Pick<PageProps<"/products">, "searchParams">) {
  const query = parseCatalogQuery(await searchParams);

  // Concurrently: the controls need the category list, the grid needs the products, and neither
  // waits on the other.
  const [products, categories] = await Promise.all([fetchProducts(query), fetchCategories()]);

  // A failure keeps the heading and reports itself in place, rather than handing the route to an
  // error boundary.
  if (!products.ok) {
    return <RetryPanel message={products.message} />;
  }

  const { items, total } = products.data;

  return (
    <>
      {/* A failed category fetch drops the control rather than offering an empty one. */}
      <CatalogFilters query={query} categories={categories.ok ? categories.categories : null} />

      <div className="mt-8">
        <p className="text-sm text-muted">
          {total} {total === 1 ? "product" : "products"}
        </p>
        <div className="mt-6">
          {items.length === 0 ? (
            // Nothing matched, which is a different thing from an empty catalog — and the one
            // `US-1.3` asks to report with a way out.
            isFiltered(query) ? (
              <EmptyState
                title="No products match"
                description="Try a broader search, or remove a filter."
                action={
                  <Link
                    href="/products"
                    className="inline-flex min-h-11 items-center rounded-lg bg-primary px-6 text-primary-ink"
                  >
                    Clear all filters
                  </Link>
                }
              />
            ) : (
              <EmptyState title="No products yet" />
            )
          ) : (
            <ProductGrid products={items} />
          )}
        </div>
        <Pagination page={query.page} totalPages={pageCount(total)} query={query} />
      </div>
    </>
  );
}
