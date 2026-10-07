"use client";

import Image from "next/image";
import Link from "next/link";

import { formatIdr } from "@/lib/format";
import { useAuth } from "@/lib/auth";
import { useCart } from "@/lib/cart";

export default function CartPage() {
  const { user, ready } = useAuth();
  const { cart, update, remove } = useCart();

  if (!ready) {
    return <p className="text-neutral-600">Loading…</p>;
  }

  if (!user) {
    return (
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Cart</h1>
        <p className="mt-2 text-neutral-600">
          Please{" "}
          <Link href="/login" className="text-emerald-800 underline hover:text-emerald-900">
            sign in
          </Link>{" "}
          to use your cart.
        </p>
      </div>
    );
  }

  const items = cart?.items ?? [];

  return (
    <div className="max-w-3xl">
      <h1 className="text-2xl font-semibold tracking-tight">Cart</h1>

      {items.length === 0 ? (
        <p className="mt-4 text-neutral-600">
          Your cart is empty.{" "}
          <Link href="/products" className="text-emerald-800 underline hover:text-emerald-900">
            Continue shopping
          </Link>
          .
        </p>
      ) : (
        <>
          <ul className="mt-6 divide-y divide-neutral-200 rounded-md border border-neutral-200 bg-white">
            {items.map((item) => (
              <li key={item.id} className="flex items-center gap-4 px-4 py-4">
                <div className="relative h-16 w-16 shrink-0 overflow-hidden rounded-md bg-neutral-100">
                  {item.image ? (
                    <Image src={item.image} alt={item.product_title} fill sizes="64px" className="object-cover" />
                  ) : null}
                </div>
                <div className="flex-1">
                  <Link href={`/products/${item.product_slug}`} className="text-sm font-medium hover:underline">
                    {item.product_title}
                  </Link>
                  <p className="text-sm text-neutral-500">{item.variant_name}</p>
                </div>
                <input
                  type="number"
                  min={1}
                  value={item.quantity}
                  onChange={(event) =>
                    void update(item.id, Math.max(1, Number(event.target.value) || 1))
                  }
                  aria-label={`Quantity for ${item.product_title}`}
                  className="w-16 rounded-md border border-neutral-300 px-2 py-1 text-sm"
                />
                <span className="w-28 text-right text-sm text-neutral-700">
                  {formatIdr(item.line_total)}
                </span>
                <button
                  type="button"
                  onClick={() => void remove(item.id)}
                  className="text-sm text-neutral-500 hover:text-red-600"
                >
                  Remove
                </button>
              </li>
            ))}
          </ul>

          <div className="mt-6 flex items-center justify-between">
            <span className="text-sm text-neutral-500">
              {cart?.items.length} line{items.length === 1 ? "" : "s"}
            </span>
            <span className="text-lg font-medium">Subtotal {formatIdr(cart?.subtotal ?? 0)}</span>
          </div>

          <Link
            href="/checkout"
            className="mt-4 inline-block w-full rounded-md bg-emerald-800 px-6 py-3 text-center text-sm font-medium text-white transition hover:bg-emerald-900 sm:w-auto"
          >
            Checkout
          </Link>
        </>
      )}
    </div>
  );
}
