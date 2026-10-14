import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";

import { fetchCredits } from "@/api/client";
import { RetryPanel } from "@/components/retry-panel";
import { licenceUrl } from "@/lib/licences";

export const metadata: Metadata = {
  title: "Image credits — LYSHEIM",
  description: "Attribution for every photograph used in the LYSHEIM catalog.",
};

/**
 * The image credits page (`US-6.1`, a licensing requirement): the attribution for every shipped
 * image, carried from the manifest `ADR-0012` keeps as the provenance record.
 *
 * The opening paragraph is doing real work rather than filling space. `ADR-0012` notes that the page
 * "doubles as an honest statement of how the demo was assembled", so it says plainly where the
 * photographs come from and that the licensees are recorded as the source lists them, rather than
 * implying a stock library.
 */
export default function CreditsPage() {
  return (
    <main className="mx-auto max-w-3xl px-6 py-16">
      <h1 className="text-4xl">Image credits</h1>
      <p className="mt-4 max-w-measure text-muted">
        Every photograph in this catalog is a Creative Commons work, used under the terms of its
        licence and credited below. Titles, creators and licences are recorded exactly as the source
        manifest lists them.
      </p>
      <Link
        href="/products"
        className="mt-8 inline-flex min-h-11 items-center text-primary underline-offset-4 hover:text-ink hover:underline"
      >
        Back to the catalog
      </Link>
      <Suspense fallback={<CreditsSkeleton />}>
        <CreditsList />
      </Suspense>
    </main>
  );
}

async function CreditsList() {
  const result = await fetchCredits();

  if (!result.ok) {
    return <RetryPanel message={result.message} />;
  }

  const { credits } = result;

  return (
    <div className="mt-12">
      <p className="text-sm text-muted">
        {credits.length} {credits.length === 1 ? "image" : "images"}
      </p>
      <ul className="mt-6 flex flex-col divide-y divide-border border-y border-border">
        {credits.map((credit) => {
          const deed = licenceUrl(credit.license);

          return (
            <li
              // The source page is unique per credit in the data model, so it is a stable key.
              key={credit.source_page_url}
              className="flex flex-col gap-1 py-4"
            >
              <cite>{credit.title}</cite>
              <p className="text-sm text-muted">
                {credit.creator} ·{" "}
                {deed ? (
                  <a
                    href={deed}
                    className="text-primary underline underline-offset-4"
                    aria-label={`Licence ${credit.license}, opens the Creative Commons deed`}
                  >
                    {credit.license}
                  </a>
                ) : (
                  credit.license
                )}{" "}
                · {credit.source} ·{" "}
                <a
                  href={credit.source_page_url}
                  className="text-primary underline underline-offset-4"
                  // Forty-six links reading "source" are indistinguishable to a screen reader on
                  // their own, so each one names the image it belongs to.
                  aria-label={`View the source of ${credit.title}`}
                >
                  source
                </a>
              </p>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

/** The list's loading state. It reserves a handful of rows; the real list is long and below the fold. */
function CreditsSkeleton() {
  return (
    <div role="status" className="mt-12">
      <span className="sr-only">Loading image credits…</span>
      <div aria-hidden="true" className="flex flex-col gap-2">
        <div className="h-5 w-24 rounded bg-border/60" />
        <div className="mt-4 flex flex-col divide-y divide-border border-y border-border">
          {Array.from({ length: 8 }, (_, index) => (
            <div key={index} className="flex flex-col gap-2 py-4">
              <div className="h-4 w-2/3 rounded bg-border/60" />
              <div className="h-3 w-1/2 rounded bg-border/60" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
