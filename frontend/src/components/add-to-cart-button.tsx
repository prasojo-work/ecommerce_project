"use client";

import Link from "next/link";
import { useState } from "react";

import { addToCart } from "@/api/cart";
import { messageForFailure } from "@/lib/api-failure";
import { firstPurchasableVariantId, type Variant } from "@/lib/cart";
import { formatPrice } from "@/lib/money";

/**
 * The add-to-cart action (`US-3.1`), which held a disabled placeholder from `M1.6` until now.
 *
 * **The colour choice is not decoration.** Every product in the catalog carries three colour
 * variants with stock and price of their own, so a button that added "the product" would have to
 * invent which one — and `catalog/models.py` is explicit that the product's price is the display
 * price while the variant's is the one a purchase is made at. Each option therefore carries its own
 * price, and an option with no stock is refused before the request rather than by it.
 *
 * Feedback is text in both directions (`UX.md` section 7, `SCOPE.md` NFR-2): `role="status"` for an
 * add that worked, `role="alert"` for one the API refused — and it refused for a reason worth
 * reading, since `US-3.2`'s message names both the stock and the number asked for.
 *
 * The header's count is not updated here. `api/cart.ts` writes the cart the API answered with into
 * the store the header reads, so the count on the other side of the page follows on its own.
 */
export function AddToCartButton({ variants }: { variants: Variant[] }) {
  const [selectedId, setSelectedId] = useState<number | null>(
    // The first colour that can actually be bought, not the first one listed — some products are
    // out of stock in every colour, and that state has to be reachable without guessing.
    () => firstPurchasableVariantId(variants),
  );
  const [pending, setPending] = useState(false);
  const [failure, setFailure] = useState<string | null>(null);
  const [added, setAdded] = useState(false);

  const soldOut = selectedId === null;

  function choose(id: number): void {
    setSelectedId(id);
    // The confirmation belongs to the add that produced it: leaving it up while the customer picks
    // a different colour would claim something they have not done.
    setAdded(false);
    setFailure(null);
  }

  async function add(): Promise<void> {
    if (selectedId === null) {
      return;
    }

    setPending(true);
    setFailure(null);
    setAdded(false);

    const outcome = await addToCart(selectedId, 1);

    setPending(false);

    if (!outcome.ok) {
      setFailure(messageForFailure(outcome.status, outcome.message));
      return;
    }

    setAdded(true);
  }

  return (
    <div className="flex flex-col items-start gap-3">
      {variants.length > 0 && (
        <fieldset className="flex w-full max-w-measure flex-col gap-2">
          {/* "Choose a colour" rather than "Colour": the detail list above already has a row called
              Colour, and it describes the product rather than the SKU being bought. */}
          <legend className="text-sm text-muted">Choose a colour</legend>
          {variants.map((variant) => (
            <label
              key={variant.id}
              className="flex min-h-11 items-center gap-3 rounded-lg border border-border bg-surface px-3 has-checked:border-primary"
            >
              <input
                type="radio"
                name="variant"
                value={variant.id}
                checked={selectedId === variant.id}
                disabled={!variant.in_stock}
                onChange={() => choose(variant.id)}
                className="size-4"
              />
              <span className={variant.in_stock ? undefined : "text-muted"}>{variant.name}</span>
              <span className="ml-auto text-sm text-muted">{formatPrice(variant.price)}</span>
              {!variant.in_stock && <span className="text-sm text-danger">Out of stock</span>}
            </label>
          ))}
        </fieldset>
      )}

      <button
        type="button"
        onClick={() => void add()}
        disabled={pending || soldOut}
        aria-describedby={soldOut ? "add-to-cart-note" : undefined}
        className="inline-flex min-h-11 items-center rounded-lg bg-primary px-6 text-primary-ink disabled:opacity-60"
      >
        {pending ? "Adding…" : "Add to cart"}
      </button>

      {/* The disabled button's reason, in text beside it: a control that does not say why reads as
          broken (`M1.6` made the same call for the placeholder this replaces). */}
      {soldOut && (
        <p id="add-to-cart-note" className="text-sm text-muted">
          {variants.length === 0
            ? "This product cannot be ordered yet."
            : "Out of stock in every colour."}
        </p>
      )}

      {failure !== null && (
        <p role="alert" className="text-sm text-danger">
          {failure}
        </p>
      )}

      {added && (
        <p role="status" className="text-sm text-success">
          Added to your cart.{" "}
          <Link href="/cart" className="text-primary underline">
            View cart
          </Link>
        </p>
      )}
    </div>
  );
}
