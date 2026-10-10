/**
 * One placeholder tile, the same shape as `ProductCard`.
 *
 * Shared by the catalogue grid and the home page's featured grid, so the two reservations cannot
 * drift apart from the card they stand in for — a skeleton that is even slightly the wrong height
 * is worse than none, because it promises a layout it does not hold.
 */
export function ProductCardSkeleton() {
  return (
    <div className="flex flex-col gap-3">
      <div className="aspect-[4/3] rounded-2xl bg-border/60" />
      <div className="h-5 w-3/4 rounded bg-border/60" />
      <div className="h-4 w-1/3 rounded bg-border/60" />
    </div>
  );
}
