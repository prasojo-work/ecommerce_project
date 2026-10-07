import Link from "next/link";

import { ProductGallery } from "@/components/ProductGallery";
import type { ProductDetail } from "@/lib/api";
import { formatIdr } from "@/lib/format";

export function ProductDetailView({ product }: { product: ProductDetail }) {
  const activeVariants = product.variants.filter((variant) => variant.is_active);
  const pricedVariants = activeVariants.length > 0 ? activeVariants : product.variants;
  const priceFrom =
    pricedVariants.length > 0
      ? Math.min(...pricedVariants.map((variant) => variant.price))
      : product.base_price;

  return (
    <div>
      <nav className="mb-6 text-sm text-neutral-500">
        <Link href="/products" className="hover:text-emerald-800">
          Shop
        </Link>
        <span className="mx-2">/</span>
        <span>{product.category.name}</span>
      </nav>

      <div className="grid gap-10 lg:grid-cols-2">
        <ProductGallery images={product.images} title={product.title} />

        <div>
          <p className="text-xs tracking-wide text-neutral-500 uppercase">{product.brand}</p>
          <h1 className="mt-1 text-3xl font-semibold tracking-tight">{product.title}</h1>
          <p className="mt-4 text-2xl font-medium">{formatIdr(priceFrom)}</p>
          <p className="mt-6 whitespace-pre-line text-neutral-700">{product.description}</p>

          {product.variants.length > 0 ? (
            <div className="mt-8">
              <h2 className="text-sm font-medium text-neutral-900">
                {product.variants.length} {product.variants.length === 1 ? "option" : "options"}
              </h2>
              <ul className="mt-3 divide-y divide-neutral-200 rounded-md border border-neutral-200">
                {product.variants.map((variant) => (
                  <li
                    key={variant.id}
                    className="flex items-center justify-between px-4 py-3 text-sm"
                  >
                    <span className="font-medium text-neutral-900">{variant.name}</span>
                    <span className="flex items-center gap-3">
                      <span className="text-neutral-700">{formatIdr(variant.price)}</span>
                      <span
                        className={variant.stock_qty > 0 ? "text-emerald-700" : "text-neutral-400"}
                      >
                        {variant.stock_qty > 0 ? "In stock" : "Out of stock"}
                      </span>
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          <button
            type="button"
            disabled
            className="mt-8 w-full cursor-not-allowed rounded-md bg-neutral-300 px-6 py-3 text-sm font-medium text-white sm:w-auto"
          >
            Add to cart (coming soon)
          </button>
        </div>
      </div>
    </div>
  );
}
