import Image from "next/image";
import Link from "next/link";

import type { ProductCard as ProductCardData } from "@/api/client";
import { formatPrice } from "@/lib/money";

/**
 * One tile in the catalog grid.
 *
 * `US-1.1` fixes the contents: image, name, price. Availability is left to the detail page, where
 * `US-1.2` asks for it. The whole tile is a single link, so it is one tab stop with a target well
 * over the 44 px `UX.md` section 7 asks for, and the product detail route it points at now exists.
 *
 * `object-contain`, not `object-cover`: `ADR-0012` excludes `BY-ND` images from cropping, 8 of the
 * 46 shipped images are `BY-ND`, and the payload carries no licence to branch on — so nothing is
 * cropped anywhere. See `ProductGallery` for the same rule.
 */
export function ProductCard({ product }: { product: ProductCardData }) {
  return (
    <article>
      <Link href={`/products/${product.slug}`} className="group flex flex-col gap-3">
        <div className="relative aspect-[4/3] overflow-hidden rounded-2xl bg-surface">
          {product.image ? (
            <Image
              src={product.image.path}
              // The data model carries `alt` per image; an empty value means decorative
              // (`UX.md` section 7), which is how Next.js should be told too.
              alt={product.image.alt}
              fill
              sizes="(min-width: 1280px) 288px, (min-width: 1024px) 33vw, (min-width: 640px) 50vw, 100vw"
              className="object-contain"
            />
          ) : null}
        </div>
        <div className="flex flex-col gap-1">
          <h3 className="text-base group-hover:underline">{product.name}</h3>
          <p className="text-sm text-muted">{formatPrice(product.price)}</p>
        </div>
      </Link>
    </article>
  );
}
