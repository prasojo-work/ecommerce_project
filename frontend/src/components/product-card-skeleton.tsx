/**
 * One placeholder tile, the same shape as `ProductCard`.
 *
 * Shared by the catalogue grid and the home page's featured grid, so the two reservations cannot
 * drift apart from the card they stand in for — a skeleton that is even slightly the wrong height
 * is worse than none, because it promises a layout it does not hold.
 *
 * It mirrors the `M7.4` tile exactly: a square frame, then the hairline rule and the three-line meta
 * block (name, spec line, price). The price row is taller than the other two because the real one is
 * set in the display family at `text-xl`.
 */
export function ProductCardSkeleton() {
  return (
    <div className="flex flex-col">
      <div className="aspect-square rounded-lg bg-border/60" />
      <div className="mt-3 flex flex-col gap-1 border-t border-border pt-3">
        <div className="h-5 w-3/4 rounded bg-border/60" />
        <div className="h-3 w-1/2 rounded bg-border/60" />
        <div className="mt-1 h-6 w-1/3 rounded bg-border/60" />
      </div>
    </div>
  );
}
