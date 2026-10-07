"use client";

import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";

import type { Category } from "@/lib/api";
import { buildCatalogQuery, DEFAULT_SORT } from "@/lib/url";

const SORT_OPTIONS = [
  { value: DEFAULT_SORT, label: "Newest" },
  { value: "price", label: "Price: low to high" },
  { value: "-price", label: "Price: high to low" },
  { value: "title", label: "Name: A to Z" },
];

const controlClass =
  "rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm text-neutral-900 focus:border-emerald-700 focus:outline-none";

export function CatalogFilters({
  categories,
  q,
  category,
  sort,
}: {
  categories: Category[];
  q: string;
  category: string;
  sort: string;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [query, setQuery] = useState(q);

  function navigate(next: { q: string; category: string; sort: string }) {
    router.push(`${pathname}${buildCatalogQuery({}, next)}`);
  }

  return (
    <form
      role="search"
      onSubmit={(event) => {
        event.preventDefault();
        navigate({ q: query.trim(), category, sort });
      }}
      className="mb-6 flex flex-wrap items-center gap-3"
    >
      <input
        type="search"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder="Search products"
        aria-label="Search products"
        className={`${controlClass} min-w-48 flex-1`}
      />
      <select
        aria-label="Category"
        value={category}
        onChange={(event) => navigate({ q: query.trim(), category: event.target.value, sort })}
        className={controlClass}
      >
        <option value="">All categories</option>
        {categories.map((item) => (
          <option key={item.id} value={item.slug}>
            {item.name}
          </option>
        ))}
      </select>
      <select
        aria-label="Sort by"
        value={sort}
        onChange={(event) => navigate({ q: query.trim(), category, sort: event.target.value })}
        className={controlClass}
      >
        {SORT_OPTIONS.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      <button
        type="submit"
        className="rounded-md bg-emerald-800 px-4 py-2 text-sm font-medium text-white transition hover:bg-emerald-900"
      >
        Search
      </button>
    </form>
  );
}
