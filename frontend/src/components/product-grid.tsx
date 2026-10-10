import type { ProductCard as ProductCardData } from "@/api/client";

import { ProductCard } from "./product-card";

/**
 * The grid columns, in one place.
 *
 * `UX.md` section 8 fixes the breakpoints and `ADR-0013` fixes the token set, but neither
 * specifies a column count, so this is the decision: one column on the smallest screens for the
 * large imagery `UX.md` section 1 asks for, then two, three, and four.
 *
 * Exported because the loading skeleton has to reserve the identical shape — a mismatch would
 * move the grid when the data lands.
 */
export const GRID_COLUMNS = "grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4";

export function ProductGrid({ products }: { products: ProductCardData[] }) {
  return (
    <ul className={GRID_COLUMNS}>
      {products.map((product) => (
        <li key={product.id}>
          <ProductCard product={product} />
        </li>
      ))}
    </ul>
  );
}
