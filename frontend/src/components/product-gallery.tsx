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
 * alteration", and no licence reaches the payload for the UI to branch on. The shipped set is
 * currently 33 `BY`, 11 `BY-SA`, 1 `PDM` and 1 `CC0` with no `BY-ND` at all — curation drops those
 * images rather than editing them — but nothing in the payload would tell the UI if that changed, so
 * the rule does not depend on it staying true. The cost is letterboxing, and the source ratios are
 * genuinely mixed (4:3, 3:2, 3:4, square), so it costs less than it sounds. `ProductCard` follows the
 * same rule.
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
