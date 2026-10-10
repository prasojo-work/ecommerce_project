/**
 * The detail page's loading state — `UX.md` section 5 asks for a skeleton.
 *
 * The two-column shape mirrors the loaded page so nothing moves when the data lands. Hidden from
 * assistive technology, with the state announced once instead.
 */
export function ProductDetailSkeleton() {
  return (
    <div role="status" className="mt-8">
      <span className="sr-only">Loading product…</span>
      <div aria-hidden="true" className="grid grid-cols-1 gap-10 md:grid-cols-2">
        <div className="aspect-square rounded-2xl bg-border/60 sm:aspect-[4/3]" />
        <div className="flex flex-col gap-6">
          <div className="flex flex-col gap-3">
            <div className="h-8 w-2/3 rounded bg-border/60" />
            <div className="h-6 w-1/4 rounded bg-border/60" />
            <div className="h-4 w-20 rounded bg-border/60" />
          </div>
          <div className="flex flex-col gap-2">
            <div className="h-4 w-full rounded bg-border/60" />
            <div className="h-4 w-full rounded bg-border/60" />
            <div className="h-4 w-1/2 rounded bg-border/60" />
          </div>
          <div className="h-11 w-40 rounded-lg bg-border/60" />
        </div>
      </div>
    </div>
  );
}
