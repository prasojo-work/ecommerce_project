import Image from "next/image";

import type { ProductDetail } from "@/api/client";

/**
 * The product gallery (`US-1.2`), named in the `UX.md` section 6 inventory.
 *
 * `M1.6` ships one image per product: the source set holds exactly one per keyword, and the
 * deferral of multi-image galleries is recorded in the changelog. It still renders from the image
 * list, so a product with more images later is a data change rather than a rewrite.
 *
 * `object-contain`, never `object-cover`. `ADR-0012` excludes `BY-ND` images "from any cropping or
 * alteration", the payload carries no licence for the UI to branch on, and 8 of the 46 shipped
 * images are `BY-ND` — so nothing may be cropped. The cost is letterboxing, because the source
 * ratios are genuinely mixed (4:3, 3:2, 3:4, square). `ProductCard` follows the same rule.
 *
 * `priority` because this image is the page's LCP candidate (`NFR-1`).
 */
export function ProductGallery({ images }: { images: ProductDetail["images"] }) {
  const [primary] = images ?? [];
  if (!primary) {
    return null;
  }

  return (
    <div className="relative aspect-square overflow-hidden rounded-2xl bg-surface sm:aspect-[4/3]">
      <Image
        src={primary.path}
        alt={primary.alt}
        fill
        priority
        sizes="(min-width: 768px) 50vw, 100vw"
        className="object-contain"
      />
    </div>
  );
}
