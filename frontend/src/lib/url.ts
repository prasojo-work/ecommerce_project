export const DEFAULT_SORT = "newest";

export type FilterValues = {
  q?: string;
  category?: string;
  sort?: string;
  page?: number;
};

export function buildCatalogQuery(
  current: FilterValues,
  overrides: Partial<FilterValues> = {},
): string {
  const merged: FilterValues = { ...current, ...overrides };
  const params = new URLSearchParams();
  if (merged.q) params.set("q", merged.q);
  if (merged.category) params.set("category", merged.category);
  if (merged.sort && merged.sort !== DEFAULT_SORT) params.set("sort", merged.sort);
  if (merged.page && merged.page > 1) params.set("page", String(merged.page));
  const suffix = params.toString();
  return suffix ? `?${suffix}` : "";
}
