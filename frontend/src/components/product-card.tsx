import Image from "next/image";

import type { ProductCard as ProductCardData } from "@/api/client";
import { formatPrice } from "@/lib/money";

/**
 * One tile in the catalog grid.
 *
 * `US-1.1` fixes the contents: image, name, price. Availability and the link to the detail page
 * arrive with `US-1.2` at `M1.6`, so the card is not interactive yet — a link would point at a
 * route that does not exist.
 */
export function ProductCard({ product }: { product: ProductCardData }) {
  return (
    <article className="flex flex-col gap-3">
      <div className="relative aspect-[4/3] overflow-hidden rounded-2xl bg-surface">
        {product.image ? (
          <Image
            src={product.image.path}
            // The data model carries `alt` per image; an empty value means decorative
            // (`UX.md` section 7), which is how Next.js should be told too.
            alt={product.image.alt}
            fill
            sizes="(min-width: 1280px) 288px, (min-width: 1024px) 33vw, (min-width: 640px) 50vw, 100vw"
            className="object-cover"
          />
        ) : null}
      </div>
      <div className="flex flex-col gap-1">
        <h3 className="text-base">{product.name}</h3>
        <p className="text-sm text-muted">{formatPrice(product.price)}</p>
      </div>
    </article>
  );
}
