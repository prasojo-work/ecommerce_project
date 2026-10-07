"use client";

import type { ReactNode } from "react";
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import {
  type Cart,
  addCartItem,
  fetchCart,
  removeCartItem,
  updateCartItem,
} from "@/lib/api";
import { useAuth } from "@/lib/auth";

export type CartState = {
  cart: Cart | null;
  count: number;
  add: (variantId: number, quantity: number) => Promise<void>;
  update: (itemId: number, quantity: number) => Promise<void>;
  remove: (itemId: number) => Promise<void>;
  refresh: () => Promise<void>;
};

const CartContext = createContext<CartState | null>(null);

export function CartProvider({ children }: { children: ReactNode }) {
  const { accessToken, ready } = useAuth();
  const [cart, setCart] = useState<Cart | null>(null);

  useEffect(() => {
    if (!ready || !accessToken) return;
    let active = true;
    fetchCart(accessToken)
      .then((data) => {
        if (active) setCart(data);
      })
      .catch(() => undefined);
    return () => {
      active = false;
    };
  }, [accessToken, ready]);

  const add = useCallback(
    async (variantId: number, quantity: number) => {
      if (!accessToken) return;
      setCart(await addCartItem(accessToken, variantId, quantity));
    },
    [accessToken],
  );

  const update = useCallback(
    async (itemId: number, quantity: number) => {
      if (!accessToken) return;
      setCart(await updateCartItem(accessToken, itemId, quantity));
    },
    [accessToken],
  );

  const remove = useCallback(
    async (itemId: number) => {
      if (!accessToken) return;
      setCart(await removeCartItem(accessToken, itemId));
    },
    [accessToken],
  );

  const refresh = useCallback(async () => {
    if (!accessToken) return;
    setCart(await fetchCart(accessToken));
  }, [accessToken]);

  const visibleCart = accessToken ? cart : null;
  const count = visibleCart?.items.reduce((total, item) => total + item.quantity, 0) ?? 0;

  const value = useMemo<CartState>(
    () => ({ cart: visibleCart, count, add, update, remove, refresh }),
    [visibleCart, count, add, update, remove, refresh],
  );

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

export function useCart(): CartState {
  const context = useContext(CartContext);
  if (context === null) {
    throw new Error("useCart must be used within a CartProvider");
  }
  return context;
}
