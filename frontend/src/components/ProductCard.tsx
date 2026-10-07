import Image from "next/image";
import Link from "next/link";

import type { ProductListItem } from "@/lib/api";
import { formatIdr } from "@/lib/format";

export function ProductCard({
  product,
  priority = false,
}: {
  product: ProductListItem;
  priority?: boolean;
}) {
  return (
    <Link href={`/products/${product.slug}`} className="group block">
      <div className="relative aspect-4/3 overflow-hidden rounded-md bg-neutral-100">
        {product.image ? (
          <Image
            src={product.image}
            alt={product.title}
            fill
            priority={priority}
            sizes="(max-width: 640px) 50vw, (max-width: 1024px) 33vw, 25vw"
            className="object-cover transition duration-300 group-hover:scale-105"
          />
        ) : null}
      </div>
      <p className="mt-3 text-xs tracking-wide text-neutral-500 uppercase">
        {product.category.name}
      </p>
      <h3 className="text-sm font-medium text-neutral-900">{product.title}</h3>
      <p className="mt-1 text-sm text-neutral-600">From {formatIdr(product.price_from)}</p>
    </Link>
  );
}
