"use client";

import { useCallback, useEffect, useSyncExternalStore, type ReactNode } from "react";

import { loadCart } from "@/api/cart";
import { clearCart, getCart, getCartFailure, subscribeToCart, type Cart } from "@/lib/cart";

import { useSession } from "./session-provider";

/**
 * The cart, kept in step with the session (`US-3.1`, `US-3.5`).
 *
 * The state lives in `lib/cart.ts` — the cart *and* the reason the last read failed, because those
 * two are read together and cleared together. This component is only the lifecycle: when a session
 * appears, read the cart; when it ends, forget it.
 *
 * It is a provider rather than something each page does for itself because the header shows the
 * count on *every* page. A page that loaded its own cart would leave the header stale everywhere
 * else, and two of them loading at once would ask the API twice for the same number.
 *
 * The three session states each decide something different, and the middle one is the one that
 * bites:
 *
 * - **`restoring`** — the access token is on its way back from the refresh cookie. Nothing is read
 *   (there is no token yet) and nothing is cleared either: clearing here would throw away a cart
 *   that is about to be read again, on every single navigation.
 * - **`authenticated`** — read it, so the count is right on the first render after a reload.
 * - **`anonymous`** — forget it, cart and failure both. This store outlives the account in it, and
 *   the next person to sign in on this tab must not see the previous shopper's count.
 */
export function CartProvider({ children }: { children: ReactNode }) {
  const { status } = useSession();

  const reload = useCallback((): void => {
    // Then, not now: `loadCart` writes what it found into the store, and the store is what notifies
    // React. Nothing here sets state in the effect body, which is also what keeps this honest to
    // `react-hooks/set-state-in-effect` rather than merely quiet to it.
    void (async () => {
      await loadCart();
    })();
  }, []);

  useEffect(() => {
    if (status === "authenticated") {
      reload();
      return;
    }

    if (status === "anonymous") {
      clearCart();
    }
  }, [status, reload]);

  return <>{children}</>;
}

export type CartValue = {
  cart: Cart | null;
  /**
   * Why the last read failed, or `null`.
   *
   * Read it only when `cart` is `null`: a failure that a later successful read or add has overtaken
   * says nothing about the cart a customer is looking at.
   */
  failure: string | null;
};

/**
 * Both values are read from the store, so a component showing either re-renders when either moves.
 * Each snapshot is a value the store replaces rather than mutates, which is what
 * `useSyncExternalStore` requires to avoid rendering the same state twice.
 */
export function useCart(): CartValue {
  const cart = useSyncExternalStore(subscribeToCart, getCart, getCart);
  const failure = useSyncExternalStore(subscribeToCart, getCartFailure, getCartFailure);

  return { cart, failure };
}
