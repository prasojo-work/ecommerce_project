import Link from "next/link";

/**
 * The detail page's not-found state.
 *
 * `UX.md` section 5 gives the PDP no empty state — "n/a (404 page)" — so this is what a withdrawn
 * or mistyped slug gets. It exists because a bare 404 is a dead end: there is no header navigation
 * until the site shell arrives, so the page has to offer the way back itself.
 */
export default function ProductNotFound() {
  return (
    <main className="mx-auto max-w-6xl px-6 py-24">
      <h1 className="text-3xl">We couldn&apos;t find that product</h1>
      <p className="mt-3 max-w-measure text-muted">
        It may have been renamed or withdrawn. The catalog has everything currently on offer.
      </p>
      <Link
        href="/products"
        className="mt-6 inline-flex min-h-11 items-center rounded-lg bg-primary px-6 text-primary-ink"
      >
        Browse the catalog
      </Link>
    </main>
  );
}
