"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { type FormEvent, useEffect, useState } from "react";

import {
  type Address,
  type ShippingOptions,
  createOrder,
  fetchAddresses,
  fetchShippingOptions,
  payWithMock,
} from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useCart } from "@/lib/cart";
import { formatIdr } from "@/lib/format";
import { newIdempotencyKey } from "@/lib/orders";

export default function CheckoutPage() {
  const router = useRouter();
  const { user, accessToken, ready } = useAuth();
  const { cart, refresh } = useCart();

  const [addresses, setAddresses] = useState<Address[]>([]);
  const [shipping, setShipping] = useState<ShippingOptions | null>(null);
  const [addressId, setAddressId] = useState<number | null>(null);
  const [shippingCode, setShippingCode] = useState("");
  const [simulateFailure, setSimulateFailure] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [idempotencyKey] = useState(newIdempotencyKey);

  useEffect(() => {
    if (!accessToken) return;
    let active = true;
    Promise.all([fetchAddresses(accessToken), fetchShippingOptions(accessToken)])
      .then(([loadedAddresses, loadedShipping]) => {
        if (!active) return;
        setAddresses(loadedAddresses);
        setShipping(loadedShipping);
        setAddressId(
          loadedAddresses.find((row) => row.is_default)?.id ?? loadedAddresses[0]?.id ?? null,
        );
        setShippingCode((current) => current || loadedShipping.options[0]?.code || "");
      })
      .catch(() => undefined);
    return () => {
      active = false;
    };
  }, [accessToken]);

  const items = cart?.items ?? [];
  const subtotal = cart?.subtotal ?? 0;
  const selected = shipping?.options.find((option) => option.code === shippingCode) ?? null;
  const total = subtotal + (selected?.cost ?? 0);

  async function handlePay(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!accessToken || addressId === null || !selected) return;
    setBusy(true);
    setError(null);
    try {
      const order = await createOrder(accessToken, {
        address_id: addressId,
        shipping_method: selected.code,
        idempotency_key: idempotencyKey,
      });
      await refresh();
      await payWithMock(accessToken, order.number, simulateFailure);
      router.push(`/orders/${order.number}`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not place the order.");
      setBusy(false);
    }
  }

  if (!ready) {
    return <p className="text-neutral-600">Loading…</p>;
  }

  if (!user) {
    return (
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Checkout</h1>
        <p className="mt-2 text-neutral-600">
          Please{" "}
          <Link href="/login" className="text-emerald-800 hover:underline">
            sign in
          </Link>{" "}
          to check out.
        </p>
      </div>
    );
  }

  if (items.length === 0 && !busy) {
    return (
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Checkout</h1>
        <p className="mt-2 text-neutral-600">
          Your cart is empty.{" "}
          <Link href="/products" className="text-emerald-800 hover:underline">
            Continue shopping
          </Link>
          .
        </p>
      </div>
    );
  }

  return (
    <div className="max-w-3xl">
      <h1 className="text-2xl font-semibold tracking-tight">Checkout</h1>

      <form onSubmit={handlePay} className="mt-6 space-y-8">
        <section>
          <h2 className="text-lg font-medium">1. Delivery address</h2>
          {addresses.length === 0 ? (
            <p className="mt-2 text-sm text-neutral-600">
              No saved address yet.{" "}
              <Link href="/account" className="text-emerald-800 hover:underline">
                Add one in your account
              </Link>{" "}
              first.
            </p>
          ) : (
            <ul className="mt-3 space-y-2">
              {addresses.map((address) => (
                <li key={address.id}>
                  <label className="flex cursor-pointer items-start gap-3 rounded-md border border-neutral-200 bg-white px-4 py-3 text-sm">
                    <input
                      type="radio"
                      name="address"
                      value={address.id}
                      checked={addressId === address.id}
                      onChange={() => setAddressId(address.id)}
                      className="mt-1"
                    />
                    <span>
                      <span className="font-medium">{address.recipient}</span>
                      {address.is_default ? (
                        <span className="ml-2 text-xs text-emerald-700">Default</span>
                      ) : null}
                      <br />
                      <span className="text-neutral-600">
                        {address.line1}, {address.city}, {address.province}{" "}
                        {address.postal_code}
                      </span>
                    </span>
                  </label>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section>
          <h2 className="text-lg font-medium">2. Shipping</h2>
          <p className="mt-1 text-sm text-neutral-600">
            Free standard delivery over {formatIdr(shipping?.free_shipping_threshold ?? 0)}.
          </p>
          <ul className="mt-3 space-y-2">
            {(shipping?.options ?? []).map((option) => (
              <li key={option.code}>
                <label className="flex cursor-pointer items-center justify-between gap-3 rounded-md border border-neutral-200 bg-white px-4 py-3 text-sm">
                  <span className="flex items-center gap-3">
                    <input
                      type="radio"
                      name="shipping"
                      value={option.code}
                      checked={shippingCode === option.code}
                      onChange={() => setShippingCode(option.code)}
                    />
                    <span>
                      <span className="font-medium">{option.name}</span>
                      <br />
                      <span className="text-neutral-600">{option.eta}</span>
                    </span>
                  </span>
                  <span className="font-medium">
                    {option.cost === 0 ? "Free" : formatIdr(option.cost)}
                  </span>
                </label>
              </li>
            ))}
          </ul>
        </section>

        <section>
          <h2 className="text-lg font-medium">3. Order summary</h2>
          <ul className="mt-3 divide-y divide-neutral-200 rounded-md border border-neutral-200 bg-white">
            {items.map((item) => (
              <li key={item.id} className="flex justify-between gap-4 px-4 py-3 text-sm">
                <span>
                  {item.quantity} × {item.product_title}
                  <br />
                  <span className="text-neutral-600">{item.variant_name}</span>
                </span>
                <span className="text-neutral-700">{formatIdr(item.line_total)}</span>
              </li>
            ))}
          </ul>
          <dl className="mt-3 space-y-1 text-sm">
            <div className="flex justify-between">
              <dt className="text-neutral-600">Subtotal</dt>
              <dd>{formatIdr(subtotal)}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-neutral-600">Shipping</dt>
              <dd>{selected?.cost === 0 ? "Free" : formatIdr(selected?.cost ?? 0)}</dd>
            </div>
            <div className="flex justify-between border-t border-neutral-200 pt-2 text-base font-medium">
              <dt>Total</dt>
              <dd>{formatIdr(total)}</dd>
            </div>
          </dl>
        </section>

        <section>
          <h2 className="text-lg font-medium">4. Payment</h2>
          <p className="mt-1 text-sm text-neutral-600">
            Demo store — payments are simulated. No card is charged.
          </p>
          <label className="mt-3 flex items-center gap-2 text-sm text-neutral-600">
            <input
              type="checkbox"
              checked={simulateFailure}
              onChange={(event) => setSimulateFailure(event.target.checked)}
            />
            Simulate a declined payment (demo)
          </label>
          {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}
          <button
            type="submit"
            disabled={busy || addressId === null || !selected}
            className="mt-4 w-full rounded-md bg-emerald-800 px-6 py-3 text-sm font-medium text-white transition hover:bg-emerald-900 disabled:opacity-60 sm:w-auto"
          >
            {busy ? "Processing…" : `Pay ${formatIdr(total)} (demo)`}
          </button>
        </section>
      </form>
    </div>
  );
}
