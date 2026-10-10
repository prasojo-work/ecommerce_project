import Link from "next/link";

import { toQueryParams, type CatalogQuery } from "@/lib/catalog-query";

/**
 * Catalog pagination (`UX.md` section 5: the success state is "grid + result count").
 *
 * Links rather than buttons, so paging works with no client JavaScript, is keyboard operable for
 * free, and keeps the page number in the URL. Every link carries the current filters, which is what
 * makes page three of a filtered view shareable (`US-1.4`) rather than quietly unfiltered.
 */
export function Pagination({
  page,
  totalPages,
  query,
}: {
  page: number;
  totalPages: number;
  query: CatalogQuery;
}) {
  if (totalPages <= 1) {
    return null;
  }

  return (
    <nav aria-label="Pagination" className="mt-12 flex items-center justify-between gap-4">
      <PageControl query={query} page={page - 1} enabled={page > 1} label="Previous" rel="prev" />
      <p className="text-sm text-muted">
        Page {page} of {totalPages}
      </p>
      <PageControl
        query={query}
        page={page + 1}
        enabled={page < totalPages}
        label="Next"
        rel="next"
      />
    </nav>
  );
}

const CONTROL_CLASSES = "inline-flex min-h-11 items-center rounded-lg border border-border px-4";

/**
 * A step in the pager. At the ends the control is a span rather than a link: there is no page to
 * go to, and a link that goes nowhere is worse than an obvious dead end. `aria-disabled` carries
 * that to assistive technology without relying on the muted colour alone (`SCOPE.md` NFR-2).
 */
function PageControl({
  query,
  page,
  enabled,
  label,
  rel,
}: {
  query: CatalogQuery;
  page: number;
  enabled: boolean;
  label: string;
  rel: "prev" | "next";
}) {
  if (!enabled) {
    return (
      <span aria-disabled="true" className={`${CONTROL_CLASSES} text-muted/60`}>
        {label}
      </span>
    );
  }

  return (
    <Link
      href={{ pathname: "/products", query: toQueryParams(query, page) }}
      rel={rel}
      className={CONTROL_CLASSES}
    >
      {label}
    </Link>
  );
}
