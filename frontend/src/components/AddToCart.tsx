"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import type { ProductVariant } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useCart } from "@/lib/cart";

export function AddToCart({ variants }: { variants: ProductVariant[] }) {
  const router = useRouter();
  const { user, ready } = useAuth();
  const { add } = useCart();
  const [variantId, setVariantId] = useState(variants[0]?.id ?? 0);
  const [quantity, setQuantity] = useState(1);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function handleAdd() {
    if (!ready) return;
    if (!user) {
      router.push("/login");
      return;
    }
    setBusy(true);
    setMessage(null);
    try {
      await add(variantId, quantity);
      setMessage("Added to cart.");
    } catch (caught) {
      setMessage(caught instanceof Error ? caught.message : "Could not add to cart.");
    } finally {
      setBusy(false);
    }
  }

  if (variants.length === 0) {
    return <p className="mt-8 text-sm text-neutral-500">Currently unavailable.</p>;
  }

  return (
    <div className="mt-8">
      <div className="flex flex-wrap items-end gap-3">
        <label className="text-sm font-medium">
          Option
          <select
            value={variantId}
            onChange={(event) => setVariantId(Number(event.target.value))}
            className="mt-1 block rounded-md border border-neutral-300 px-3 py-2 text-sm"
          >
            {variants.map((variant) => (
              <option key={variant.id} value={variant.id}>
                {variant.name}
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm font-medium">
          Quantity
          <input
            type="number"
            min={1}
            value={quantity}
            onChange={(event) => setQuantity(Math.max(1, Number(event.target.value) || 1))}
            className="mt-1 block w-20 rounded-md border border-neutral-300 px-3 py-2 text-sm"
          />
        </label>
        <button
          type="button"
          onClick={() => void handleAdd()}
          disabled={busy}
          className="rounded-md bg-emerald-800 px-6 py-3 text-sm font-medium text-white transition hover:bg-emerald-900 disabled:opacity-60"
        >
          {busy ? "Adding…" : "Add to cart"}
        </button>
      </div>
      {message ? <p className="mt-3 text-sm text-neutral-600">{message}</p> : null}
    </div>
  );
}
