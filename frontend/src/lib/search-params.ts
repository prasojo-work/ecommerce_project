/**
 * The query parameters of a request, as Next hands them to a page.
 *
 * A repeated parameter (`?page=1&page=2`) arrives as an array, and a parameter with no value still
 * arrives as an empty string.
 */
export type SearchParams = Record<string, string | string[] | undefined>;

/**
 * The first value of a parameter, or `undefined` when it is absent.
 *
 * Every reader wants one value rather than a union to unwrap at each use, so the unwrapping lives
 * here instead of being reinvented by each of them.
 */
export function firstValue(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}
