import { GRID_COLUMNS } from "./product-grid";
import { PAGE_SIZE } from "@/lib/pagination";

/**
 * The catalog loading state: `UX.md` section 5 asks for card skeletons.
 *
 * This is the `<Suspense>` fallback, so it ships inside the prerendered shell while the listing
 * streams in. It reserves `PAGE_SIZE` cards because that is exactly how many arrive — a smaller
 * count would let the grid grow as it fills and shift the page.
 *
 * The placeholders are hidden from assistive technology and the state is announced once instead,
 * so a screen reader hears "Loading products" rather than twenty-four empty boxes.
 */
export function ProductGridSkeleton({ count = PAGE_SIZE }: { count?: number }) {
  return (
    <div role="status" className="mt-8">
      <span className="sr-only">Loading products…</span>
      <div aria-hidden="true" className="flex flex-col gap-8">
        {/* Reserves the result-count line, so the first row of products does not jump. */}
        <div className="h-5 w-24 rounded bg-border/60" />
        <div className={GRID_COLUMNS}>
          {Array.from({ length: count }, (_, index) => (
            <div key={index} className="flex flex-col gap-3">
              <div className="aspect-[4/3] rounded-2xl bg-border/60" />
              <div className="h-5 w-3/4 rounded bg-border/60" />
              <div className="h-4 w-1/3 rounded bg-border/60" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
