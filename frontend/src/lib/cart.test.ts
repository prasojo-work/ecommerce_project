import { beforeEach, describe, expect, it, vi } from "vitest";

import type { Cart, CartLine, Variant } from "./cart";
import {
  canDecrease,
  canIncrease,
  clearCart,
  firstPurchasableVariantId,
  getCart,
  getCartFailure,
  linesOf,
  setCart,
  setCartFailure,
  subscribeToCart,
  unitsIn,
} from "./cart";

const LINE: CartLine = {
  id: 1,
  variant_id: 10,
  product_name: "Heia Ash Shelving Unit",
  product_slug: "heia-ash-shelving-unit",
  variant_name: "Clay",
  sku: "HEIA-CLAY",
  unit_price: { amount_cents: 12000, currency: "USD" },
  line_total: { amount_cents: 24000, currency: "USD" },
  quantity: 2,
  available_stock: 5,
  image_path: "/images/shelving.webp",
};

function cartWith(lines: CartLine[]): Cart {
  return {
    id: 1,
    items: lines,
    item_count: lines.reduce((total, line) => total + line.quantity, 0),
    subtotal: { amount_cents: 24000, currency: "USD" },
  };
}

function variant(id: number, inStock: boolean): Variant {
  return {
    id,
    in_stock: inStock,
    name: `Colour ${String(id)}`,
    price: { amount_cents: 12000, currency: "USD" },
    sku: `SKU-${String(id)}`,
    stock_qty: inStock ? 3 : 0,
  };
}

beforeEach(() => {
  // The store is module state, so it outlives a test unless it is emptied.
  clearCart();
});

describe("the cart store", () => {
  it("starts empty rather than with an empty cart, which is a different thing", () => {
    expect(getCart()).toBeNull();
  });

  it("notifies subscribers when a cart arrives", () => {
    const listener = vi.fn();
    const unsubscribe = subscribeToCart(listener);
    const cart = cartWith([LINE]);

    setCart(cart);

    expect(getCart()).toEqual(cart);
    expect(listener).toHaveBeenCalledTimes(1);
    unsubscribe();
  });

  it("notifies subscribers when the cart is cleared, so no one keeps showing a stale count", () => {
    setCart(cartWith([LINE]));
    const listener = vi.fn();
    const unsubscribe = subscribeToCart(listener);

    clearCart();

    expect(getCart()).toBeNull();
    expect(listener).toHaveBeenCalledTimes(1);
    unsubscribe();
  });

  it("stops notifying once a subscriber has gone away", () => {
    const listener = vi.fn();
    const unsubscribe = subscribeToCart(listener);
    unsubscribe();

    setCart(cartWith([LINE]));

    expect(listener).not.toHaveBeenCalled();
  });

  it("remembers why a read failed, so a page has something to say", () => {
    setCartFailure("The cart service could not be reached.");

    expect(getCartFailure()).toBe("The cart service could not be reached.");
  });

  it("notifies subscribers when a failure is recorded", () => {
    const listener = vi.fn();
    const unsubscribe = subscribeToCart(listener);

    setCartFailure("The cart service could not be reached.");

    expect(listener).toHaveBeenCalledTimes(1);
    unsubscribe();
  });

  it("forgets the failure when a cart arrives, so a working cart is never covered by one", () => {
    // The read that failed may have been overtaken by an add that worked. Leaving the message up
    // would put a retry panel on top of a cart that is on screen and correct.
    setCartFailure("The cart service could not be reached.");

    setCart(cartWith([LINE]));

    expect(getCartFailure()).toBeNull();
  });

  it("forgets the failure when the session ends, so it cannot outlive the account", () => {
    setCartFailure("The cart service could not be reached.");

    clearCart();

    expect(getCartFailure()).toBeNull();
  });
});

describe("linesOf", () => {
  it("answers with the lines the API sent", () => {
    expect(linesOf(cartWith([LINE]))).toEqual([LINE]);
  });

  it("answers with no lines for a cart that has none, and for no cart at all", () => {
    // `items` is optional in the schema, so both the absent list and the absent cart have to read
    // the same way: a page that crashed on either would crash on the very first visit.
    expect(linesOf(cartWith([]))).toEqual([]);
    expect(linesOf({ ...cartWith([]), items: undefined })).toEqual([]);
    expect(linesOf(null)).toEqual([]);
  });
});

describe("unitsIn", () => {
  it("counts units rather than lines, which is what the API's own count does", () => {
    expect(unitsIn(cartWith([LINE, { ...LINE, id: 2, variant_id: 11, quantity: 3 }]))).toBe(5);
  });

  it("counts nothing for a cart that has not been read yet", () => {
    expect(unitsIn(null)).toBe(0);
  });
});

describe("canIncrease / canDecrease", () => {
  it("allows an increase while stock covers the next one", () => {
    expect(canIncrease({ ...LINE, quantity: 1, available_stock: 5 })).toBe(true);
  });

  it("refuses an increase once the line holds all the available stock (`US-3.2`)", () => {
    expect(canIncrease({ ...LINE, quantity: 5, available_stock: 5 })).toBe(false);
  });

  it("refuses an increase on a line whose stock has since gone to zero", () => {
    // Stock moves underneath a cart. The API is the authority at checkout, but a stepper that
    // offered a number the API would refuse is a button that exists to fail.
    expect(canIncrease({ ...LINE, quantity: 1, available_stock: 0 })).toBe(false);
  });

  it("allows a decrease above one and refuses it at one", () => {
    expect(canDecrease({ ...LINE, quantity: 2 })).toBe(true);
    expect(canDecrease({ ...LINE, quantity: 1 })).toBe(false);
  });
});

describe("firstPurchasableVariantId", () => {
  it("offers the first variant that is in stock", () => {
    expect(firstPurchasableVariantId([variant(1, true), variant(2, false)])).toBe(1);
  });

  it("skips the variants that are not, rather than offering the first row", () => {
    expect(firstPurchasableVariantId([variant(1, false), variant(2, true)])).toBe(2);
  });

  it("offers nothing when no variant can be bought, which is a product out of stock", () => {
    expect(firstPurchasableVariantId([variant(1, false), variant(2, false)])).toBeNull();
  });

  it("offers nothing for a product with no variants at all", () => {
    expect(firstPurchasableVariantId([])).toBeNull();
  });
});
