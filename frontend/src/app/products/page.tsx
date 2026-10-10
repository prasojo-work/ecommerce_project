import type { Metadata } from "next";
import { Suspense } from "react";

import { fetchProducts } from "@/api/client";
import { EmptyState } from "@/components/empty-state";
import { Pagination } from "@/components/pagination";
import { ProductGrid } from "@/components/product-grid";
import { ProductGridSkeleton } from "@/components/product-grid-skeleton";
import { RetryPanel } from "@/components/retry-panel";
import { PAGE_SIZE, pageCount, parsePage } from "@/lib/pagination";

export const metadata: Metadata = {
  title: "Catalog — LYSHEIM",
  description: "Every piece in the LYSHEIM catalog.",
};

/**
 * The catalog listing page (`UX.md` section 5: grid, pagination, card skeletons, empty state).
 *
 * The heading renders immediately and everything that depends on the listing sits behind one
 * `<Suspense>` boundary: the result count, the grid, and the pager. That boundary is doing double
 * duty. It is the loading state, and with `cacheComponents: true` it is also required — the
 * uncached fetch and the `searchParams` read below would otherwise be a build-time error, because
 * they cannot be resolved while the static shell is prerendered.
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
  const page = parsePage((await searchParams).page);
  const result = await fetchProducts(page, PAGE_SIZE);

  // A failure keeps the heading and the page furniture and reports itself in place, rather than
  // handing the whole route to an error boundary.
  if (!result.ok) {
    return <RetryPanel message={result.message} />;
  }

  const { items, total } = result.data;

  // The pager is rendered even when this page is empty. The API answers a page past the end with
  // an empty page rather than a `404` so the client can handle it without special-casing, and
  // dropping the pager here would strand a visitor who arrived on such a URL.
  return (
    <div className="mt-8">
      <p className="text-sm text-muted">
        {total} {total === 1 ? "product" : "products"}
      </p>
      <div className="mt-6">
        {items.length === 0 ? (
          <EmptyState title="No products yet" />
        ) : (
          <ProductGrid products={items} />
        )}
      </div>
      <Pagination page={page} totalPages={pageCount(total)} />
    </div>
  );
}
