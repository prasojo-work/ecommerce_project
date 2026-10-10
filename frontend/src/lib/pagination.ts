/**
 * A page of the catalog grid.
 *
 * The API defaults `page_size` to 24, but the client sends it explicitly: the grid decides its
 * own density, and the loading skeleton has to reserve exactly as many cards as will arrive, or
 * the page shifts when the data lands.
 */
export const PAGE_SIZE = 24;

/**
 * Read `?page=` into a page number the API accepts.
 *
 * The API answers a `page` below 1 with a `400` (`API.md` section 4), so anything unusable —
 * missing, non-numeric, zero, negative — falls back to page one rather than being sent. A page
 * *past* the end is deliberately not corrected here: the API returns an empty page for it rather
 * than a `404`, which is what lets the storefront render its no-products state.
 */
export function parsePage(value: string | string[] | undefined): number {
  const raw = Array.isArray(value) ? value[0] : value;
  if (raw === undefined) {
    return 1;
  }

  const parsed = Number.parseInt(raw, 10);
  return Number.isInteger(parsed) && parsed >= 1 ? parsed : 1;
}

/** Number of pages a result set spans. Never below 1, so an empty catalog still has a page one. */
export function pageCount(total: number, pageSize: number = PAGE_SIZE): number {
  return Math.max(1, Math.ceil(total / pageSize));
}
