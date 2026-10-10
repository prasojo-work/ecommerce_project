import Link from "next/link";
import type { ReactNode } from "react";

import { SortSelect } from "./sort-select";
import { flattenCategories, type CategoryNode } from "@/lib/categories";
import {
  PRICE_BANDS,
  bandParams,
  isBandActive,
  isFiltered,
  toQueryParams,
  type CatalogQuery,
  type PriceBand,
} from "@/lib/catalog-query";

const FIELD_CLASSES =
  "min-h-11 w-full rounded-lg border border-border bg-surface px-3 text-base text-ink";

/**
 * `CatalogFilters`, named in the `UX.md` section 6 inventory.
 *
 * One GET form, which is what `US-1.4` asks for almost literally: submitting it puts every control
 * in the URL, so a filtered view is shareable and the back button steps back through filter states.
 * It also works with JavaScript switched off.
 *
 * The price bands are links rather than form controls because a band is *two* parameters. A radio
 * group or a select could only submit one value, which would mean inventing a second vocabulary for
 * the URL that could no longer round-trip a hand-typed `min_price`/`max_price` — and the URL is the
 * thing `US-1.4` requires to be shareable.
 *
 * The price bounds ride along as hidden inputs so applying a search cannot silently drop the price
 * filter, and the band links carry the other filters for the same reason in the other direction.
 *
 * `UX.md` section 8 asks for filters to "collapse into a drawer on mobile". This is that collapse
 * as a `<details>`: always open on a wide screen, and on a phone the reader decides. A true overlay
 * drawer — focus trap, scroll lock, focus return — is deferred to the `M6.2` accessibility pass,
 * where its behaviour can be tested rather than guessed.
 */
export function CatalogFilters({
  query,
  categories,
}: {
  query: CatalogQuery;
  categories: CategoryNode[] | null;
}) {
  const flat = flattenCategories(categories ?? []);

  return (
    <form
      method="get"
      action="/products"
      className="mt-8 flex flex-col gap-4 rounded-2xl border border-border bg-surface p-4"
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
        <div className="flex flex-1 flex-col gap-1">
          <label htmlFor="catalog-q" className="text-sm text-muted">
            Search
          </label>
          <input
            id="catalog-q"
            type="search"
            name="q"
            // Keyed by the submitted value so a back-button navigation re-mounts the field with the
            // value that belongs to the URL, which an uncontrolled input would otherwise keep stale.
            key={query.q ?? ""}
            defaultValue={query.q ?? ""}
            placeholder="Chair, oak, lamp…"
            className={FIELD_CLASSES}
          />
        </div>
        <button
          type="submit"
          className="inline-flex min-h-11 items-center justify-center rounded-lg bg-primary px-6 text-primary-ink"
        >
          Apply
        </button>
      </div>

      <details open>
        <summary className="cursor-pointer py-3 text-sm text-muted">Filters</summary>
        <div className="flex flex-col gap-4">
          <div className="grid gap-4 sm:grid-cols-2">
            {categories ? (
              <div className="flex flex-col gap-1">
                <label htmlFor="catalog-category" className="text-sm text-muted">
                  Category
                </label>
                <select
                  id="catalog-category"
                  name="category"
                  key={query.category ?? ""}
                  defaultValue={query.category ?? ""}
                  className={FIELD_CLASSES}
                >
                  <option value="">All categories</option>
                  {flat.map((category) => (
                    <option key={category.slug} value={category.slug}>
                      {category.depth > 0
                        ? `${"— ".repeat(category.depth)}${category.name}`
                        : category.name}
                    </option>
                  ))}
                </select>
              </div>
            ) : null}

            <div className="flex flex-col gap-1">
              <label htmlFor="catalog-sort" className="text-sm text-muted">
                Sort
              </label>
              <SortSelect value={query.sort} />
            </div>
          </div>

          <fieldset className="flex flex-col gap-2">
            <legend className="text-sm text-muted">Price</legend>
            <ul className="flex flex-wrap gap-2">
              <li>
                <PriceBandLink query={query} band={null}>
                  Any price
                </PriceBandLink>
              </li>
              {PRICE_BANDS.map((band) => (
                <li key={band.label}>
                  <PriceBandLink query={query} band={band}>
                    {band.label}
                  </PriceBandLink>
                </li>
              ))}
            </ul>
          </fieldset>

          {query.minPrice !== undefined ? (
            <input type="hidden" name="min_price" value={query.minPrice} />
          ) : null}
          {query.maxPrice !== undefined ? (
            <input type="hidden" name="max_price" value={query.maxPrice} />
          ) : null}
        </div>
      </details>

      {isFiltered(query) ? (
        <Link
          href="/products"
          className="inline-flex min-h-11 items-center self-start text-sm text-primary underline-offset-4 hover:underline"
        >
          Clear all filters
        </Link>
      ) : null}
    </form>
  );
}

/**
 * One price band, as a link that keeps the other filters and resets paging.
 *
 * A band replaces the price filter rather than adding to it, so the bounds are rebuilt from scratch
 * instead of merged — otherwise choosing "Any price" would leave the previous bounds behind in the
 * URL. `aria-current` carries the selection to assistive technology, and the active link is also
 * heavier and bordered, so the state is never signalled by colour alone (`SCOPE.md` NFR-2).
 */
function PriceBandLink({
  query,
  band,
  children,
}: {
  query: CatalogQuery;
  band: PriceBand | null;
  children: ReactNode;
}) {
  const active = isBandActive(query, band);
  const params = {
    ...toQueryParams({ ...query, page: 1, minPrice: undefined, maxPrice: undefined }),
    ...bandParams(band),
  };

  return (
    <Link
      href={{ pathname: "/products", query: params }}
      aria-current={active ? "true" : undefined}
      className={`inline-flex min-h-11 items-center rounded-lg border px-4 text-sm ${
        active
          ? "border-primary bg-primary font-semibold text-primary-ink"
          : "border-border text-ink"
      }`}
    >
      {children}
    </Link>
  );
}
