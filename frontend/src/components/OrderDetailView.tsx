"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { OrderStatusBadge } from "@/components/OrderStatusBadge";
import { type Order, fetchOrder, payWithMock } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { formatIdr } from "@/lib/format";
import { formatOrderDate } from "@/lib/orders";

export function OrderDetailView({ number }: { number: string }) {
  const { user, accessToken, ready } = useAuth();
  const [order, setOrder] = useState<Order | null>(null);
  const [missing, setMissing] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!accessToken) return;
    let active = true;
    fetchOrder(accessToken, number)
      .then((data) => {
        if (active) setOrder(data);
      })
      .catch(() => {
        if (active) setMissing(true);
      });
    return () => {
      active = false;
    };
  }, [accessToken, number]);

  async function handlePay(again: boolean) {
    if (!accessToken) return;
    setBusy(true);
    setError(null);
    try {
      await payWithMock(accessToken, number, again);
      setOrder(await fetchOrder(accessToken, number));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Payment failed. Please retry.");
    } finally {
      setBusy(false);
    }
  }

  if (!ready) {
    return <p className="text-neutral-600">Loading…</p>;
  }

  if (!user) {
    return (
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Order</h1>
        <p className="mt-2 text-neutral-600">
          Please{" "}
          <Link href="/login" className="text-emerald-800 underline hover:text-emerald-900">
            sign in
          </Link>{" "}
          to see this order.
        </p>
      </div>
    );
  }

  if (missing) {
    return (
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Order not found</h1>
        <p className="mt-2 text-neutral-600">
          <Link href="/orders" className="text-emerald-800 underline hover:text-emerald-900">
            Back to your orders
          </Link>
        </p>
      </div>
    );
  }

  if (!order) {
    return <p className="text-neutral-600">Loading…</p>;
  }

  return (
    <div className="max-w-3xl">
      <p className="text-sm text-neutral-600">
        <Link href="/orders" className="hover:underline">
          Orders
        </Link>{" "}
        / {order.number}
      </p>
      <div className="mt-2 flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-semibold tracking-tight">{order.number}</h1>
        <OrderStatusBadge status={order.status} />
      </div>
      <p className="mt-1 text-sm text-neutral-600">Placed {formatOrderDate(order.created_at)}</p>

      {order.status === "pending_payment" ? (
        <div className="mt-6 rounded-md border border-amber-200 bg-amber-50 px-4 py-4">
          <p className="text-sm text-amber-900">
            This order is not paid yet. Demo store — no real charge is made.
          </p>
          {error ? <p className="mt-2 text-sm text-red-700">{error}</p> : null}
          <div className="mt-3 flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => void handlePay(false)}
              disabled={busy}
              className="rounded-md bg-emerald-800 px-4 py-2 text-sm font-medium text-white transition hover:bg-emerald-900 disabled:opacity-60"
            >
              {busy ? "Processing…" : `Pay ${formatIdr(order.total)} (demo)`}
            </button>
            <button
              type="button"
              onClick={() => void handlePay(true)}
              disabled={busy}
              className="rounded-md border border-neutral-300 bg-white px-4 py-2 text-sm font-medium text-neutral-700 transition hover:border-neutral-400 disabled:opacity-60"
            >
              Simulate a declined payment
            </button>
          </div>
        </div>
      ) : null}

      <h2 className="mt-8 text-lg font-medium">Items</h2>
      <ul className="mt-3 divide-y divide-neutral-200 rounded-md border border-neutral-200 bg-white">
        {order.items.map((item) => (
          <li key={item.id} className="flex justify-between gap-4 px-4 py-3 text-sm">
            <span>
              {item.quantity} × {item.product_title}
              <br />
              <span className="text-neutral-600">
                {item.variant_name} · {formatIdr(item.unit_price)} each
              </span>
            </span>
            <span className="text-neutral-700">{formatIdr(item.line_total)}</span>
          </li>
        ))}
      </ul>

      <dl className="mt-3 space-y-1 text-sm">
        <div className="flex justify-between">
          <dt className="text-neutral-600">Subtotal</dt>
          <dd>{formatIdr(order.subtotal)}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-neutral-600">
            Shipping — {order.shipping_method_name}
          </dt>
          <dd>{order.shipping_cost === 0 ? "Free" : formatIdr(order.shipping_cost)}</dd>
        </div>
        <div className="flex justify-between border-t border-neutral-200 pt-2 text-base font-medium">
          <dt>Total</dt>
          <dd>{formatIdr(order.total)}</dd>
        </div>
      </dl>

      <h2 className="mt-8 text-lg font-medium">Delivery address</h2>
      <p className="mt-2 text-sm text-neutral-600">
        {order.shipping_address.recipient}
        <br />
        {order.shipping_address.line1}
        {order.shipping_address.line2 ? `, ${order.shipping_address.line2}` : ""}
        <br />
        {order.shipping_address.city}, {order.shipping_address.province}{" "}
        {order.shipping_address.postal_code}
        <br />
        {order.shipping_address.country}
        <br />
        {order.shipping_address.phone}
      </p>
    </div>
  );
}
