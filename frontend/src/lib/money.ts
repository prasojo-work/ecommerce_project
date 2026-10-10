import type { components } from "@/api/schema";

type Money = components["schemas"]["MoneySchema"];

/**
 * Format a money payload for display.
 *
 * `UX.md` section 9 fixes the format (`$1,240.00`), and `API.md` section 1 carries an explicit
 * `currency` on every amount even though the store sells in one currency today — so this reads
 * the field rather than assuming USD, and a second currency would not render as dollars.
 */
export function formatPrice(money: Money): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: money.currency,
  }).format(money.amount_cents / 100);
}
