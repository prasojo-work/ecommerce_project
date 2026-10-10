"use client";

import { useRouter } from "next/navigation";
import { useTransition } from "react";

/**
 * The "fix" half of the catalog error state.
 *
 * A client component because it is genuinely interactive, which is the bar `ARCHITECTURE.md`
 * section 5 sets. `router.refresh()` re-runs the route's server render, so the retry makes a real
 * request — unlike a link back to the same URL, which the router may satisfy without one.
 */
export function RetryButton() {
  const router = useRouter();
  const [isRetrying, startRetry] = useTransition();

  return (
    <button
      type="button"
      disabled={isRetrying}
      onClick={() => startRetry(() => router.refresh())}
      className="mt-6 inline-flex min-h-11 items-center rounded-lg bg-primary px-6 text-primary-ink disabled:opacity-60"
    >
      {/* The label changes too, so the pending state is not signalled by colour alone. */}
      {isRetrying ? "Trying again…" : "Try again"}
    </button>
  );
}
