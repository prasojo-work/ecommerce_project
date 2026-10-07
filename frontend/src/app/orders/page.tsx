"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { OrderStatusBadge } from "@/components/OrderStatusBadge";
import { type OrderSummary, fetchOrders } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { formatIdr } from "@/lib/format";
import { formatOrderDate } from "@/lib/orders";

export default function OrdersPage() {
  const { user, accessToken, ready } = useAuth();
  const [orders, setOrders] = useState<OrderSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!accessToken) return;
    let active = true;
    fetchOrders(accessToken)
      .then((data) => {
        if (active) setOrders(data.results);
      })
      .catch(() => undefined)
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [accessToken]);

  if (!ready) {
    return <p className="text-neutral-600">Loading…</p>;
  }

  if (!user) {
    return (
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Orders</h1>
        <p className="mt-2 text-neutral-600">
          Please{" "}
          <Link href="/login" className="text-emerald-800 hover:underline">
            sign in
          </Link>{" "}
          to see your orders.
        </p>
      </div>
    );
  }

  return (
    <div className="max-w-3xl">
      <h1 className="text-2xl font-semibold tracking-tight">Orders</h1>

      {loading ? (
        <p className="mt-4 text-neutral-600">Loading…</p>
      ) : orders.length === 0 ? (
        <p className="mt-4 text-neutral-600">
          You have not placed an order yet.{" "}
          <Link href="/products" className="text-emerald-800 hover:underline">
            Continue shopping
          </Link>
          .
        </p>
      ) : (
        <ul className="mt-6 divide-y divide-neutral-200 rounded-md border border-neutral-200 bg-white">
          {orders.map((order) => (
            <li key={order.number} className="flex items-center justify-between gap-4 px-4 py-4">
              <Link href={`/orders/${order.number}`} className="text-sm hover:underline">
                <span className="font-medium">{order.number}</span>
                <br />
                <span className="text-neutral-600">
                  {formatOrderDate(order.created_at)} · {order.item_count} item
                  {order.item_count === 1 ? "" : "s"}
                </span>
              </Link>
              <span className="flex items-center gap-4">
                <span className="text-sm text-neutral-700">{formatIdr(order.total)}</span>
                <OrderStatusBadge status={order.status} />
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
