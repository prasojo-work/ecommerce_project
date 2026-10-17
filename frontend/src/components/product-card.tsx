import Image from "next/image";
import Link from "next/link";

import type { ProductCard as ProductCardData } from "@/api/client";
import { formatPrice } from "@/lib/money";

/**
 * One tile in the catalog grid.
 *
 * `US-1.1` fixed the contents: image, name, price. `UX-DIRECTION.md` (`M7.4`) adds the **spec line**
 * — material and finish, then availability — because the tile was quiet *and* said nothing a price
 * tag could not. The buying question in this category is "will it fit, is it in stock", and the
 * answer is already in the payload for free: `material`, `color` and `in_stock` come back on
 * `ProductCardSchema` and were being discarded. `UX-GOAL-1` wants that doubt settled before the
 * cart, not after it.
 *
 * The line is assembled from the parts that exist and disappears when none do: `material` and
 * `color` are both blank-able in the model, and a tile reading `· · In stock` is worse than one
 * reading `In stock`.
 *
 * The whole tile is a single link, so it is one tab stop with a target well over the 44 px `UX.md`
 * section 7 asks for. Chrome is a hairline rule and nothing else — no card, no shadow, no radius
 * except the image frame, which is the "rules, not cards" half of `UX-DIRECTION.md` section 3.
 *
 * `object-contain`, not `object-cover`: `ADR-0012` excludes `BY-ND` images from cropping, and no
 * licence reaches the payload for the UI to branch on, so nothing is cropped anywhere. The shipped
 * set happens to contain no `BY-ND` today, because curation drops them, but the rule does not depend
 * on that staying true. See `ProductGallery` for the same reasoning. The frame is square because a
 * catalogue tile reads as a specimen square; the image inside it is still never cut.
 */
export function ProductCard({ product }: { product: ProductCardData }) {
  const finish = [product.material, product.color].filter((part) => part.length > 0).join(" · ");
  const availability = product.in_stock ? "In stock" : "Out of stock";
  const spec = finish.length > 0 ? `${finish} · ${availability}` : availability;

  return (
    <article>
      <Link href={`/products/${product.slug}`} className="group flex flex-col">
        <div className="relative aspect-square overflow-hidden rounded-lg bg-surface">
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

        <div className="mt-3 flex flex-col gap-1 border-t border-border pt-3">
          <h3 className="text-base group-hover:underline">{product.name}</h3>
          <p className="text-xs text-muted">{spec}</p>
          <p className="mt-1 font-display text-xl tabular-nums">{formatPrice(product.price)}</p>
        </div>
      </Link>
    </article>
  );
}
