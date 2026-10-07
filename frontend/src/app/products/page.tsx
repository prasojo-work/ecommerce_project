import Link from "next/link";

import { ProductCard } from "@/components/ProductCard";
import { fetchProducts } from "@/lib/api";

export const dynamic = "force-dynamic";

const PAGE_SIZE = 12;

type SearchParams = Record<string, string | string[] | undefined>;

function first(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

export default async function ProductsPage({
  searchParams,
}: {
  searchParams: Promise<SearchParams>;
}) {
  const params = await searchParams;
  const page = Math.max(1, Number(first(params.page)) || 1);
  const data = await fetchProducts({ page, page_size: PAGE_SIZE });
  const totalPages = Math.max(1, Math.ceil(data.count / data.page_size));

  return (
    <div>
      <header className="mb-6">
        <h1 className="text-2xl font-semibold tracking-tight">Shop</h1>
        <p className="mt-1 text-sm text-neutral-600">{data.count} products</p>
      </header>

      {data.results.length === 0 ? (
        <p className="text-neutral-600">No products found.</p>
      ) : (
        <div className="grid grid-cols-2 gap-6 sm:grid-cols-3 lg:grid-cols-4">
          {data.results.map((product) => (
            <ProductCard key={product.id} product={product} />
          ))}
        </div>
      )}

      {totalPages > 1 ? (
        <nav className="mt-10 flex items-center justify-center gap-4 text-sm">
          {page > 1 ? (
            <Link href={`/products?page=${page - 1}`} className="text-emerald-800 hover:underline">
              Previous
            </Link>
          ) : null}
          <span className="text-neutral-500">
            Page {page} of {totalPages}
          </span>
          {page < totalPages ? (
            <Link href={`/products?page=${page + 1}`} className="text-emerald-800 hover:underline">
              Next
            </Link>
          ) : null}
        </nav>
      ) : null}
    </div>
  );
}
