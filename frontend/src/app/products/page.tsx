import Link from "next/link";

import { CatalogFilters } from "@/components/CatalogFilters";
import { ProductCard } from "@/components/ProductCard";
import { fetchCategories, fetchProducts } from "@/lib/api";
import { buildCatalogQuery, DEFAULT_SORT } from "@/lib/url";

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
  const q = first(params.q);
  const category = first(params.category);
  const sort = first(params.sort) ?? DEFAULT_SORT;
  const page = Math.max(1, Number(first(params.page)) || 1);

  const [categories, data] = await Promise.all([
    fetchCategories(),
    fetchProducts({ q, category, sort, page, page_size: PAGE_SIZE }),
  ]);

  const totalPages = Math.max(1, Math.ceil(data.count / data.page_size));
  const filters = { q, category, sort };

  return (
    <div>
      <header className="mb-6">
        <h1 className="text-2xl font-semibold tracking-tight">Shop</h1>
        <p className="mt-1 text-sm text-neutral-600">{data.count} products</p>
      </header>

      <CatalogFilters
        categories={categories}
        q={q ?? ""}
        category={category ?? ""}
        sort={sort}
      />

      {data.results.length === 0 ? (
        <p className="text-neutral-600">No products match your search.</p>
      ) : (
        <div className="grid grid-cols-2 gap-6 sm:grid-cols-3 lg:grid-cols-4">
          {data.results.map((product, index) => (
            <ProductCard
              key={product.id}
              product={product}
              priority={index === 0}
            />
          ))}
        </div>
      )}

      {totalPages > 1 ? (
        <nav aria-label="Pagination" className="mt-10 flex items-center justify-center gap-4 text-sm">
          {page > 1 ? (
            <Link
              href={`/products${buildCatalogQuery({ ...filters, page: page - 1 })}`}
              className="text-emerald-800 hover:underline"
            >
              Previous
            </Link>
          ) : null}
          <span className="text-neutral-500">
            Page {page} of {totalPages}
          </span>
          {page < totalPages ? (
            <Link
              href={`/products${buildCatalogQuery({ ...filters, page: page + 1 })}`}
              className="text-emerald-800 hover:underline"
            >
              Next
            </Link>
          ) : null}
        </nav>
      ) : null}
    </div>
  );
}
