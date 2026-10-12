import type { components } from "@/api/schema";

/**
 * The cart, as the header's count and the cart page both need it (`US-3.1`, `US-3.4`).
 *
 * The store is a module variable read through `useSyncExternalStore`, the shape `lib/session.ts`
 * uses, because two separate places have to agree about the cart: the header's count and the cart
 * page. A payload copied into each component's state would let them disagree the moment an add
 * landed on one of them.
 *
 * **Every mutation answers with the whole cart** (`API.md` section 5), and that response is the only
 * thing written here. Totals are the API's arithmetic rather than the browser's: a client that
 * recomputed a subtotal would be a second implementation of a rule that has to agree to the cent.
 */

export type Cart = components["schemas"]["CartSchema"];
export type CartLine = components["schemas"]["CartLineSchema"];
export type Variant = components["schemas"]["VariantSchema"];

let current: Cart | null = null;
let lastFailure: string | null = null;
const listeners = new Set<() => void>();

function notify(): void {
  for (const listener of listeners) listener();
}

/** The live cart, or `null` when none has been read yet — which is not the same as an empty one. */
export function getCart(): Cart | null {
  return current;
}

/** Why the last *read* failed, or `null`. Mutations report their own failures to their caller. */
export function getCartFailure(): string | null {
  return lastFailure;
}

export function subscribeToCart(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

/**
 * Record a cart. This also clears any remembered failure, because the cart arriving answers it.
 *
 * That rule lives here rather than in each reader for the reason the store exists at all: a read
 * that failed and was then overtaken by a successful add must not leave a retry panel sitting on top
 * of a cart that is working, and two components checking for that themselves is two chances to get
 * it wrong.
 */
export function setCart(cart: Cart): void {
  current = cart;
  lastFailure = null;
  notify();
}

/**
 * Remember why a read failed.
 *
 * Held in the store rather than in the provider's state so that the lifecycle that clears it — a
 * session ending — is the same one that clears the cart, and neither can be left behind.
 */
export function setCartFailure(message: string): void {
  lastFailure = message;
  notify();
}

/**
 * Forget the cart.
 *
 * Called when a session ends, because this store outlives the account that filled it: a badge still
 * showing the previous shopper's count would be showing one person's data to the next.
 */
export function clearCart(): void {
  current = null;
  lastFailure = null;
  notify();
}

/** The lines. `items` is optional in the schema because the API sends an empty list by default. */
export function linesOf(cart: Cart | null): CartLine[] {
  return cart?.items ?? [];
}

/** The header's number: units, not lines, which is what `CartSchema.item_count` already sums. */
export function unitsIn(cart: Cart | null): number {
  return cart?.item_count ?? 0;
}

/** `US-3.2`: a line can grow while there is stock left to cover it. */
export function canIncrease(line: CartLine): boolean {
  return line.quantity < line.available_stock;
}

/**
 * A line can shrink to one and no further.
 *
 * Zero is not a quantity on this cart: removal is its own action (`US-3.3`), so a stepper that
 * reached zero would delete a line by arithmetic, with no confirmation and nothing to say so.
 */
export function canDecrease(line: CartLine): boolean {
  return line.quantity > 1;
}

/**
 * Which variant a product page offers first: the first one that can actually be bought, or none.
 *
 * Every product in the seed carries three colour variants with stock of their own, and some are out
 * of stock in all three, so "first" has to mean first *purchasable* rather than first row.
 */
export function firstPurchasableVariantId(variants: Variant[]): number | null {
  const available = variants.find((variant) => variant.in_stock);
  return available?.id ?? null;
}
