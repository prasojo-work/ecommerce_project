import { ProductCardSkeleton } from "./product-card-skeleton";
import { GRID_COLUMNS } from "./product-grid";
import { PAGE_SIZE } from "@/lib/pagination";

/**
 * The catalog loading state: `UX.md` section 5 asks for card skeletons.
 *
 * This is the `<Suspense>` fallback, so it ships inside the prerendered shell while the filters and
 * the listing stream in. It mirrors the loaded layout — filter panel, result count, then grid — and
 * reserves `PAGE_SIZE` cards because that is exactly how many arrive. A smaller count would let the
 * grid grow as it fills and shift the page.
 *
 * The placeholders are hidden from assistive technology and the state is announced once instead, so
 * a screen reader hears "Loading products" rather than twenty-four empty boxes.
 */
export function ProductGridSkeleton({ count = PAGE_SIZE }: { count?: number }) {
  return (
    <div role="status" className="mt-8">
      <span className="sr-only">Loading products…</span>
      <div aria-hidden="true" className="flex flex-col gap-8">
        <div className="flex flex-col gap-4 rounded-2xl border border-border bg-surface p-4">
          <div className="h-11 w-full rounded-lg bg-border/60 sm:w-72" />
          <div className="h-11 w-full rounded-lg bg-border/60 sm:w-48" />
          <div className="h-11 w-full rounded-lg bg-border/60 sm:w-96" />
        </div>
        {/* Reserves the result-count line, so the first row of products does not jump. */}
        <div className="h-5 w-24 rounded bg-border/60" />
        <div className={GRID_COLUMNS}>
          {Array.from({ length: count }, (_, index) => (
            <ProductCardSkeleton key={index} />
          ))}
        </div>
      </div>
    </div>
  );
}
