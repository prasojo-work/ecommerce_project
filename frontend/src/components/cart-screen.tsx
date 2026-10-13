"use client";

import Image from "next/image";
import Link from "next/link";
import { useState } from "react";

import { loadCart, removeLine, setLineQuantity } from "@/api/cart";
import { messageForFailure } from "@/lib/api-failure";
import { canDecrease, canIncrease, linesOf, type CartLine } from "@/lib/cart";
import { formatPrice } from "@/lib/money";

import { useCart } from "./cart-provider";
import { EmptyState } from "./empty-state";
import { useSession } from "./session-provider";

/**
 * `/cart` (`US-3.2`-`US-3.4`) — the client half, because everything on it is behind a token that
 * only exists in memory (`ADR-0009`), so none of it can be rendered on the server.
 *
 * The four states `UX.md` section 5 gives this screen are all here, and they are distinguished by
 * text rather than colour (`SCOPE.md` NFR-2):
 *
 * - **restoring** — the token is on its way back from the refresh cookie, so "signed out" would be a
 *   lie for exactly as long as it took to read this.
 * - **signed out** — the cart is a signed-in feature (`ADR-0017`), so this says so and offers the
 *   way in, rather than showing an empty cart that would never fill.
 * - **loading / failed** — `cart === null` with no failure is a read in flight; with one, it is a
 *   read that did not happen and a retry. The failure is only read here while there is no cart to
 *   show, so a dropped read that a later add overtook cannot cover a working cart.
 * - **empty** — the cart really is empty, which is a different thing from all three above.
 *
 * **No arithmetic happens on this page.** Every mutation answers with the whole cart (`API.md`
 * section 5), so the totals below are the API's, recomputed by the API, every time.
 */
export function CartScreen() {
  const { status } = useSession();
  const { cart, failure } = useCart();
  const [actionFailure, setActionFailure] = useState<string | null>(null);
  const [pendingLine, setPendingLine] = useState<number | null>(null);

  async function change(line: CartLine, quantity: number): Promise<void> {
    setPendingLine(line.id);
    setActionFailure(null);

    const outcome = await setLineQuantity(line.id, quantity);

    setPendingLine(null);

    if (!outcome.ok) {
      // A `409` here is `US-3.2` refusing a number above stock, and its message already names both
      // the stock and the request — so it is shown as written rather than reworded.
      setActionFailure(messageForFailure(outcome.status, outcome.message));
    }
  }

  async function remove(line: CartLine): Promise<void> {
    setPendingLine(line.id);
    setActionFailure(null);

    const outcome = await removeLine(line.id);

    setPendingLine(null);

    if (!outcome.ok) {
      setActionFailure(messageForFailure(outcome.status, outcome.message));
    }
    // Nothing to reconcile on success: the response replaced the cart in the store, and this page
    // reads the store.
  }

  if (status === "restoring") {
    return <p className="mt-10 text-muted">Loading your cart…</p>;
  }

  if (status !== "authenticated") {
    return (
      <div className="mt-10 rounded-2xl border border-dashed border-border bg-surface px-8 py-16 text-center">
        <h2 className="text-xl">Sign in to use your cart</h2>
        <p className="mx-auto mt-3 max-w-measure text-muted">
          A LYSHEIM cart belongs to your account, so it is still here the next time you sign in.
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

  if (cart === null) {
    if (failure !== null) {
      return (
        <div
          role="alert"
          className="mt-10 rounded-2xl border border-border bg-surface px-8 py-12 text-center"
        >
          <p className="mx-auto max-w-measure text-muted">{failure}</p>
          <button
            type="button"
            onClick={() => void loadCart()}
            className="mt-6 inline-flex min-h-11 items-center rounded-lg border border-border px-6"
          >
            Try again
          </button>
        </div>
      );
    }

    return <p className="mt-10 text-muted">Loading your cart…</p>;
  }

  const lines = linesOf(cart);

  if (lines.length === 0) {
    return (
      <EmptyState
        title="Your cart is empty"
        description="Browse the catalog and add something you would like to keep."
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

  return (
    <div className="mt-10 flex flex-col gap-10 lg:flex-row lg:items-start">
      <div className="flex-1">
        {actionFailure !== null && (
          <p
            role="alert"
            className="mb-6 rounded-lg border border-danger bg-surface px-4 py-3 text-sm text-danger"
          >
            {actionFailure}
          </p>
        )}

        <ul className="flex flex-col gap-6">
          {lines.map((line) => {
            const pending = pendingLine === line.id;
            const description = `${line.product_name} (${line.variant_name})`;

            return (
              <li
                key={line.id}
                className="flex flex-wrap items-start gap-4 rounded-2xl border border-border bg-surface p-4"
              >
                <div className="relative size-24 shrink-0 overflow-hidden rounded-lg">
                  {line.image_path ? (
                    // Decorative: the product's name is the text beside it, so announcing the image
                    // would only repeat it (`UX.md` section 7).
                    <Image
                      src={line.image_path}
                      alt=""
                      fill
                      sizes="96px"
                      className="object-contain"
                    />
                  ) : null}
                </div>

                <div className="flex min-w-40 flex-1 flex-col gap-1">
                  <h3 className="text-lg">
                    <Link href={`/products/${line.product_slug}`} className="hover:underline">
                      {line.product_name}
                    </Link>
                  </h3>
                  <p className="text-sm text-muted">{line.variant_name}</p>
                  <p className="text-sm">{formatPrice(line.unit_price)} each</p>
                </div>

                <div className="flex flex-col items-end gap-2">
                  <div className="flex items-center gap-1">
                    <button
                      type="button"
                      onClick={() => void change(line, line.quantity - 1)}
                      disabled={pending || !canDecrease(line)}
                      aria-label={`Decrease the quantity of ${description}`}
                      className="inline-flex size-11 items-center justify-center rounded-lg border border-border disabled:opacity-60"
                    >
                      −
                    </button>
                    {/* Text, not a spinner or a colour: the number is the fact being changed, and it
                        is the one thing a screen reader needs to hear afterwards. */}
                    <span aria-live="polite" className="min-w-10 text-center">
                      {line.quantity}
                    </span>
                    <button
                      type="button"
                      onClick={() => void change(line, line.quantity + 1)}
                      disabled={pending || !canIncrease(line)}
                      aria-label={`Increase the quantity of ${description}`}
                      className="inline-flex size-11 items-center justify-center rounded-lg border border-border disabled:opacity-60"
                    >
                      +
                    </button>
                  </div>

                  <p className="text-sm">{formatPrice(line.line_total)}</p>

                  {/* No confirmation step, unlike removing an address: a cart line is recoverable
                      by adding it again, and this control sits beside the number it changes. */}
                  <button
                    type="button"
                    onClick={() => void remove(line)}
                    disabled={pending}
                    className="min-h-11 text-sm text-primary underline disabled:opacity-60"
                  >
                    {pending ? "Working…" : "Remove"}
                  </button>

                  {/* `US-3.2` asks for stock to be respected, and the stepper refuses the number
                      rather than allowing it and reporting the refusal afterwards. Saying why it
                      will not go higher is the difference between a limit and a broken button. */}
                  {!canIncrease(line) && (
                    <p className="text-sm text-muted">
                      {line.available_stock === 0
                        ? "No stock left"
                        : `Only ${String(line.available_stock)} available`}
                    </p>
                  )}
                </div>
              </li>
            );
          })}
        </ul>
      </div>

      <aside
        aria-labelledby="summary-heading"
        className="w-full rounded-2xl border border-border bg-surface p-6 lg:w-72"
      >
        <h2 id="summary-heading" className="text-lg">
          Summary
        </h2>

        <dl className="mt-4 flex flex-col gap-2 text-sm">
          <div className="flex justify-between gap-4">
            <dt className="text-muted">Subtotal</dt>
            <dd>{formatPrice(cart.subtotal)}</dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-muted">Shipping</dt>
            {/* `API.md` section 5 carries a subtotal and no shipping: the options and their prices
                are a checkout concern (`US-4.2`, `M4.2`). A number invented here would be a quote
                this milestone cannot honour, so the cart says where it comes from instead. */}
            <dd className="text-muted">Calculated at checkout</dd>
          </div>
        </dl>

        {/* `US-3.4`'s proceed-to-checkout action, which `M4.5` gave somewhere to go. It was the
            disabled control with its reason stated for as long as it took `/checkout` to exist; now
            there is a page behind it, so it is a link. */}
        <Link
          href="/checkout"
          className="mt-6 inline-flex min-h-11 w-full items-center justify-center rounded-lg bg-primary px-6 text-primary-ink"
        >
          Proceed to checkout
        </Link>
      </aside>
    </div>
  );
}
