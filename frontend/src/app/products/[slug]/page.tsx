import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";

import { fetchProduct } from "@/api/client";
import { AddToCartButton } from "@/components/add-to-cart-button";
import { ProductDetailSkeleton } from "@/components/product-detail-skeleton";
import { ProductGallery } from "@/components/product-gallery";
import { RetryPanel } from "@/components/retry-panel";
import { dimensionParts } from "@/lib/dimensions";
import { formatPrice } from "@/lib/money";

/**
 * Per-product metadata (`US-1.2`: "correct `<title>`/metadata"; `NFR-6`: per-page metadata).
 *
 * Reading `params` and an uncached fetch are both request-time, so under Cache Components the
 * metadata streams in alongside the rest of the deferred content rather than being required for
 * the static shell. Next memoises the underlying `fetch` across this function and the page, so the
 * product is still requested once.
 *
 * `notFound()` is called here too: a product that does not exist should 404 before a title is
 * invented for it, and a crawler must not see `200` with a title for a page that isn't there.
 */
export async function generateMetadata(props: PageProps<"/products/[slug]">): Promise<Metadata> {
  const { slug } = await props.params;
  const result = await fetchProduct(slug);

  if (!result.ok) {
    if (result.kind === "not-found") {
      notFound();
    }
    return { title: "Product — LYSHEIM" };
  }

  return {
    title: `${result.product.name} — LYSHEIM`,
    description: result.product.description,
  };
}

/**
 * The product detail page (`US-1.2`).
 *
 * The back link renders from the static shell; the two-column detail streams in behind the
 * boundary, which is both the skeleton `UX.md` section 5 asks for and what Cache Components
 * requires of a request-time fetch.
 */
export default function ProductPage(props: PageProps<"/products/[slug]">) {
  return (
    <main className="mx-auto max-w-6xl px-6 py-16">
      <Link
        href="/products"
        className="text-sm text-muted underline-offset-4 hover:text-ink hover:underline"
      >
        Back to catalog
      </Link>
      <Suspense fallback={<ProductDetailSkeleton />}>
        <ProductDetail params={props.params} />
      </Suspense>
    </main>
  );
}

async function ProductDetail({ params }: Pick<PageProps<"/products/[slug]">, "params">) {
  const { slug } = await params;
  const result = await fetchProduct(slug);

  if (!result.ok) {
    if (result.kind === "not-found") {
      notFound();
    }
    return <RetryPanel message={result.message} />;
  }

  const { product } = result;
  const dimensions = dimensionParts(product);

  return (
    <div className="mt-8 grid grid-cols-1 gap-10 md:grid-cols-2">
      <ProductGallery images={product.images} />
      <div className="flex flex-col gap-6">
        <div className="flex flex-col gap-2">
          <h1 className="text-3xl">{product.name}</h1>
          <p className="text-xl">{formatPrice(product.price)}</p>
          {/* Redundant by design: the words carry the state, so the colour is not the only signal
              (`UX.md` section 7). */}
          <p
            className={`text-sm ${product.availability.in_stock ? "text-success" : "text-danger"}`}
          >
            {product.availability.in_stock ? "In stock" : "Out of stock"}
          </p>
        </div>

        <p className="max-w-measure text-muted">{product.description}</p>

        <dl className="flex max-w-measure flex-col gap-2 text-sm">
          <DetailRow label="Material" value={product.material} />
          <DetailRow label="Colour" value={product.color} />
          {dimensions.length > 0 ? (
            <DetailRow label="Dimensions" value={dimensions.join(" · ")} />
          ) : null}
        </dl>

        <AddToCartButton />
      </div>
    </div>
  );
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex gap-2">
      <dt className="text-muted">{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}
