import { parsePage } from "./pagination";
import { firstValue, type SearchParams } from "./search-params";

/**
 * The sort values `API.md` section 4 fixes, with the labels `UX.md` does not supply — it names a
 * `SortSelect` component but no options. The `-` prefix means descending, per the contract.
 */
export const SORT_OPTIONS = [
  { value: "name", label: "Name A–Z" },
  { value: "price", label: "Price, low to high" },
  { value: "-price", label: "Price, high to low" },
  { value: "newest", label: "Newest first" },
] as const;

export type Sort = (typeof SORT_OPTIONS)[number]["value"];

/**
 * The API's own default (`SortOption.NAME`). Matching it means the storefront and the API can never
 * disagree about what an unsorted listing is.
 */
export const DEFAULT_SORT: Sort = "name";

export type PriceBand = { label: string; min?: number; max?: number };

/**
 * Price bands in cents, because `US-1.4` asks for a "price band" rather than free-text bounds.
 *
 * The thresholds are measured against the shipped catalog rather than guessed: 46 products from
 * $40 to $2,185, with p25 $113, p50 $216 and p75 $837. Round numbers at $100, $250 and $750 split
 * it 11 / 13 / 8 / 14, so every band earns its place.
 *
 * A price sitting exactly on a boundary belongs to both neighbouring bands, because `max_price` is
 * inclusive (`catalog/api.py`). Clean round numbers in a shared URL are worth more than exclusivity
 * on a value no product in this catalog actually has.
 */
export const PRICE_BANDS: PriceBand[] = [
  { label: "Under $100", max: 10000 },
  { label: "$100 – $250", min: 10000, max: 25000 },
  { label: "$250 – $750", min: 25000, max: 75000 },
  { label: "Over $750", min: 75000 },
];

export type CatalogQuery = {
  page: number;
  sort: Sort;
  q?: string;
  category?: string;
  minPrice?: number;
  maxPrice?: number;
};

/** Non-negative integer cents and nothing else: the API answers anything else with a `400`. */
function parseCents(value: string | string[] | undefined): number | undefined {
  const raw = firstValue(value)?.trim();
  if (!raw || !/^\d+$/.test(raw)) {
    return undefined;
  }

  const parsed = Number.parseInt(raw, 10);
  return Number.isSafeInteger(parsed) ? parsed : undefined;
}

function parseText(value: string | string[] | undefined): string | undefined {
  const raw = firstValue(value)?.trim();
  return raw ? raw : undefined;
}

/**
 * Read the storefront's listing state out of the URL.
 *
 * Anything the API would answer with a `400` — a `sort` outside the enum, a `page` below one, a
 * bound that is not a non-negative integer — falls back to a default, exactly as `parsePage` does,
 * so a hand-edited or stale link degrades to a valid listing rather than an error panel.
 *
 * An unknown `category` is deliberately passed through. The API returns zero results for it instead
 * of erroring (`RUNBOOK.md` section 6), which is precisely the explicit no-results state `US-1.3`
 * asks the storefront to render.
 */
export function parseCatalogQuery(params: SearchParams): CatalogQuery {
  const sort = firstValue(params.sort);

  return {
    page: parsePage(params.page),
    sort: SORT_OPTIONS.some((option) => option.value === sort) ? (sort as Sort) : DEFAULT_SORT,
    q: parseText(params.q),
    category: parseText(params.category),
    minPrice: parseCents(params.min_price),
    maxPrice: parseCents(params.max_price),
  };
}

/**
 * Whether anything narrows the listing.
 *
 * This is what separates the empty catalog — "No products yet", the copy `UX.md` section 5 fixes —
 * from a search that matched nothing, which `US-1.3` wants reported with a way out.
 */
export function isFiltered(query: CatalogQuery): boolean {
  return Boolean(
    query.q || query.category || query.minPrice !== undefined || query.maxPrice !== undefined,
  );
}

/**
 * The query as URL parameters, for links, and for rebroadcasting the parts a form cannot show.
 *
 * Names come from `API.md` section 4 so the URL and the API share one vocabulary, and anything
 * sitting at its default is left out so a shared link stays short. `page` is an argument rather
 * than a field because every link that must keep the filters — the pager — chooses its own page.
 */
export function toQueryParams(
  query: CatalogQuery,
  page: number = query.page,
): Record<string, string> {
  const params: Record<string, string> = {};

  if (query.q) {
    params.q = query.q;
  }
  if (query.category) {
    params.category = query.category;
  }
  if (query.minPrice !== undefined) {
    params.min_price = String(query.minPrice);
  }
  if (query.maxPrice !== undefined) {
    params.max_price = String(query.maxPrice);
  }
  if (query.sort !== DEFAULT_SORT) {
    params.sort = query.sort;
  }
  if (page > 1) {
    params.page = String(page);
  }

  return params;
}

/** The parameters that select one band, or clear the price filter when given `null`. */
export function bandParams(band: PriceBand | null): Record<string, string> {
  if (!band) {
    return {};
  }

  const params: Record<string, string> = {};
  if (band.min !== undefined) {
    params.min_price = String(band.min);
  }
  if (band.max !== undefined) {
    params.max_price = String(band.max);
  }
  return params;
}

/** Whether a band is the one currently applied. `null` is the "any price" choice. */
export function isBandActive(query: CatalogQuery, band: PriceBand | null): boolean {
  if (!band) {
    return query.minPrice === undefined && query.maxPrice === undefined;
  }

  return query.minPrice === band.min && query.maxPrice === band.max;
}
