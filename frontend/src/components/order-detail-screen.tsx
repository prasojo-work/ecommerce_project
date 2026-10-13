"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { loadOrder, type OrderDetail } from "@/api/orders";
import { messageForFailure } from "@/lib/api-failure";
import { formatPrice } from "@/lib/money";
import { eventLabel, formatDate, statusClass, statusLabel } from "@/lib/orders";

import { EmptyState } from "./empty-state";
import { RetryPanel } from "./retry-panel";
import { useSession } from "./session-provider";

/**
 * `/orders/[number]` (`UX.md` flow E, `US-4.6`) — the client half, for the reason the history is: the
 * order is behind a token that only exists in memory (`ADR-0009`).
 *
 * The four things `US-4.6` asks for are all here — the status badge, the line items, the shipping
 * address and the totals — plus the timeline `API.md` section 6 adds to this route, because a status
 * on its own ("Shipped") says where an order is and not how it got there.
 *
 * **A `404` is its own state, not a failure.** The API answers the same `404` for an order that never
 * existed and for one that belongs to somebody else, and this page says the same thing back: that
 * there is no such order *here*. Retrying it would be pointless, so it does not offer to.
 */
export function OrderDetailScreen({ orderNumber }: { orderNumber: string }) {
  const { status } = useSession();
  const [order, setOrder] = useState<OrderDetail | null>(null);
  const [failure, setFailure] = useState<string | null>(null);
  const [missing, setMissing] = useState(false);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    if (status !== "authenticated") {
      return;
    }

    let active = true;

    void (async () => {
      const outcome = await loadOrder(orderNumber);
      if (!active) {
        return;
      }

      if (outcome.ok) {
        setOrder(outcome.order);
        setFailure(null);
        setMissing(false);
        return;
      }

      // `404` covers both "no such order" and "not yours", and the API deliberately does not say
      // which — so neither does this page.
      setMissing(outcome.status === 404);
      setOrder(null);
      setFailure(
        outcome.status === 404 ? null : messageForFailure(outcome.status, outcome.message),
      );
    })();

    return () => {
      active = false;
    };
  }, [status, orderNumber, attempt]);

  if (status === "restoring") {
    return <p className="mt-10 text-muted">Loading…</p>;
  }

  if (status !== "authenticated") {
    return (
      <div className="mt-10 rounded-2xl border border-dashed border-border bg-surface px-8 py-16 text-center">
        <h2 className="text-xl">Sign in to see this order</h2>
        <p className="mx-auto mt-3 max-w-measure text-muted">
          Orders belong to their account, so this one needs the account it was placed with.
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

  if (missing) {
    return (
      <EmptyState
        title={`No order ${orderNumber}`}
        description="There is no such order on your account. Check the number, or look through your orders."
        action={
          <Link
            href="/orders"
            className="inline-flex min-h-11 items-center rounded-lg bg-primary px-6 text-primary-ink"
          >
            See your orders
          </Link>
        }
      />
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

  if (order === null) {
    return <p className="mt-10 text-muted">Loading your order…</p>;
  }

  return (
    <article className="mt-8">
      <p className="flex flex-wrap items-center gap-3">
        <span className="text-xl font-medium">{order.number}</span>
        <span className={`rounded-full border px-3 py-1 text-sm ${statusClass(order.status)}`}>
          {statusLabel(order.status)}
        </span>
      </p>
      <p className="mt-2 text-sm text-muted">Placed {formatDate(order.placed_at)}</p>

      <h2 className="mt-8 text-lg">What you ordered</h2>
      <ul className="mt-3 flex flex-col gap-2 text-sm">
        {order.items.map((item) => (
          <li
            key={`${item.product_name}-${item.variant_name}`}
            className="flex justify-between gap-4"
          >
            <span>
              {item.quantity} × {item.product_name} ({item.variant_name})
            </span>
            <span>{formatPrice(item.line_total)}</span>
          </li>
        ))}
      </ul>

      <dl className="mt-6 max-w-sm rounded-2xl border border-border bg-surface p-6 text-sm">
        <div className="flex justify-between gap-4">
          <dt className="text-muted">Subtotal</dt>
          <dd>{formatPrice(order.subtotal)}</dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt className="text-muted">Shipping</dt>
          <dd>{formatPrice(order.shipping)}</dd>
        </div>
        <div className="mt-3 flex justify-between gap-4 border-t border-border pt-3 text-base">
          <dt>Total</dt>
          <dd className="font-medium">{formatPrice(order.total)}</dd>
        </div>
      </dl>

      <h2 className="mt-8 text-lg">Delivering to</h2>
      <p className="mt-3 text-sm text-muted">{formatAddress(order)}</p>

      <h2 className="mt-8 text-lg">Status</h2>
      <ol className="mt-3 flex flex-col gap-3 text-sm">
        {order.events.map((event) => (
          <li key={`${event.to_status}-${event.at}`} className="border-l border-border pl-4">
            <span className="font-medium">{eventLabel(event.to_status)}</span>
            <span className="block text-muted">{formatDate(event.at)}</span>
            {event.note !== "" && <span className="block text-muted">{event.note}</span>}
          </li>
        ))}
      </ol>

      <p className="mt-8">
        <Link href="/orders" className="min-h-11 text-primary underline">
          Back to your orders
        </Link>
      </p>
    </article>
  );
}

/**
 * The shipping address as one line, recipient first.
 *
 * Built from the order's own snapshot columns rather than a saved address, because that is what a
 * receipt is (`ARCHITECTURE.md` section 4): editing the address book afterwards must not rewrite
 * where last year's parcel went.
 */
function formatAddress(order: OrderDetail): string {
  const address = order.shipping_address;
  return [
    address.recipient,
    address.line1,
    address.line2,
    address.city,
    address.region,
    address.postal_code,
    address.country,
  ]
    .filter((part) => part !== "")
    .join(", ");
}
