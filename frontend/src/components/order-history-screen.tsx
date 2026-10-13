"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { loadOrders, type OrderPage } from "@/api/orders";
import { messageForFailure } from "@/lib/api-failure";
import { formatPrice } from "@/lib/money";
import { formatDate, statusClass, statusLabel } from "@/lib/orders";
import { pageCount } from "@/lib/pagination";

import { EmptyState } from "./empty-state";
import { RetryPanel } from "./retry-panel";
import { useSession } from "./session-provider";

/**
 * `/orders` (`UX.md` flow E, `US-4.5`) — the client half, because the token that reads these orders
 * only exists in memory (`ADR-0009`), so none of it can be rendered on the server.
 *
 * The states are the ones `/cart` established, and for the same reasons: **restoring** while the token
 * comes back from the refresh cookie, **signed out** rather than an empty list that would never fill,
 * and a **failure** that offers to try again instead of pretending to be an empty history. The fifth
 * is **no orders**, which is a different thing from all four.
 *
 * **Paging is a page number in this component's state, not in the URL.** The catalog puts it in the URL
 * because a filtered page three is worth sharing (`US-1.4`); a page of somebody's own order history is
 * not — the link would work only for the person it was sent to, and they can already reach it.
 */
export function OrderHistoryScreen() {
  const { status } = useSession();
  const [page, setPage] = useState(1);
  const [attempt, setAttempt] = useState(0);
  const [data, setData] = useState<OrderPage | null>(null);
  const [failure, setFailure] = useState<string | null>(null);

  useEffect(() => {
    if (status !== "authenticated") {
      return;
    }

    // A page that unmounts mid-read — a navigation away, or a second page requested first — must not
    // write its answer over the newer one.
    let active = true;

    void (async () => {
      const outcome = await loadOrders(page);
      if (!active) {
        return;
      }

      if (outcome.ok) {
        setData(outcome.page);
        setFailure(null);
        return;
      }

      setData(null);
      setFailure(messageForFailure(outcome.status, outcome.message));
    })();

    return () => {
      active = false;
    };
  }, [status, page, attempt]);

  if (status === "restoring") {
    return <p className="mt-10 text-muted">Loading…</p>;
  }

  if (status !== "authenticated") {
    return (
      <div className="mt-10 rounded-2xl border border-dashed border-border bg-surface px-8 py-16 text-center">
        <h2 className="text-xl">Sign in to see your orders</h2>
        <p className="mx-auto mt-3 max-w-measure text-muted">
          Your orders belong to your account, so we can only show them to you.
        </p>
        <p className="mt-6">
          <Link
            href="/login"
            className="inline-flex min-h-11 items-center rounded-lg bg-primary px-6 text-primary-ink"
          >
            Sign in
          </Link>
        </p>
      </div>
    );
  }

  if (failure !== null) {
    return (
      <div className="mt-8">
        <RetryPanel message={failure} />
        <button
          type="button"
          onClick={() => setAttempt(attempt + 1)}
          className="mt-4 min-h-11 text-primary underline"
        >
          Try again
        </button>
      </div>
    );
  }

  if (data === null) {
    return <p className="mt-10 text-muted">Loading your orders…</p>;
  }

  if (data.items.length === 0) {
    return (
      <EmptyState
        title="No orders yet"
        description="Once you have bought something, it will be listed here with its status."
        action={
          <Link
            href="/products"
            className="inline-flex min-h-11 items-center rounded-lg bg-primary px-6 text-primary-ink"
          >
            Browse the catalog
          </Link>
        }
      />
    );
  }

  const totalPages = pageCount(data.total, data.page_size);

  return (
    <div className="mt-8">
      <p className="text-sm text-muted">
        {data.total === 1 ? "1 order" : `${String(data.total)} orders`}
      </p>

      <ul className="mt-4 flex flex-col gap-3">
        {data.items.map((order) => (
          <li key={order.number}>
            <Link
              href={`/orders/${order.number}`}
              className="block rounded-2xl border border-border bg-surface p-4"
            >
              <span className="flex flex-wrap items-center justify-between gap-3">
                <span className="font-medium">{order.number}</span>
                <span
                  className={`rounded-full border px-3 py-1 text-sm ${statusClass(order.status)}`}
                >
                  {statusLabel(order.status)}
                </span>
              </span>
              <span className="mt-2 block text-sm text-muted">
                {formatDate(order.placed_at)} ·{" "}
                {order.item_count === 1 ? "1 item" : `${String(order.item_count)} items`} ·{" "}
                {formatPrice(order.total)}
              </span>
            </Link>
          </li>
        ))}
      </ul>

      {/* Buttons rather than the catalog's links: the page number is state here, so there is no URL
          for a link to carry. `disabled` is the honest control for an end — there is no page to go to,
          and a button that did nothing would be worse than one that says it cannot. */}
      {totalPages > 1 && (
        <nav aria-label="Pagination" className="mt-8 flex items-center justify-between gap-4">
          <button
            type="button"
            onClick={() => setPage(page - 1)}
            disabled={page <= 1}
            className="inline-flex min-h-11 items-center rounded-lg border border-border px-4 disabled:opacity-60"
          >
            Previous
          </button>
          <p className="text-sm text-muted">
            Page {page} of {totalPages}
          </p>
          <button
            type="button"
            onClick={() => setPage(page + 1)}
            disabled={page >= totalPages}
            className="inline-flex min-h-11 items-center rounded-lg border border-border px-4 disabled:opacity-60"
          >
            Next
          </button>
        </nav>
      )}
    </div>
  );
}
