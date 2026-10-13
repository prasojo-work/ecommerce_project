/**
 * What an order's status is called, and how a date on it reads (`US-4.5`, `US-4.6`).
 *
 * Both live here rather than in the components for the reason `lib/money.ts` gives: the same order is
 * rendered on the history page, on its detail page and in the checkout confirmation, and a status
 * spelled "Paid" in one place and `paid` in another is one order described as two.
 */

/**
 * `orders.models.OrderStatus`, as the API sends it.
 *
 * Typed as a union of the five the backend defines, but every reader below still tolerates a word it
 * has never seen: a status added to the model before it is added here would otherwise render as an
 * empty badge, which is worse than an unfamiliar one.
 */
export type OrderStatus = "pending" | "paid" | "shipped" | "delivered" | "cancelled";

const STATUS_LABELS: Record<OrderStatus, string> = {
  pending: "Awaiting payment",
  paid: "Paid",
  shipped: "Shipped",
  delivered: "Delivered",
  cancelled: "Cancelled",
};

/** The words a customer reads for a status. An unknown one is shown as itself, not as blank. */
export function statusLabel(status: string): string {
  return STATUS_LABELS[status as OrderStatus] ?? status;
}

/**
 * The badge's border and background.
 *
 * `cancelled` is the only status that is a problem to the person reading it — a paid order and a
 * delivered one are both good news — so it is the only one that takes the danger colour. The word is
 * always present (`SCOPE.md` NFR-2), which is what makes this reinforcement rather than the signal.
 */
export function statusClass(status: string): string {
  return status === "cancelled" ? "border-danger text-danger" : "border-border bg-surface";
}

const EVENT_LABELS: Record<OrderStatus, string> = {
  pending: "Order placed",
  paid: "Payment captured",
  shipped: "Dispatched",
  delivered: "Delivered",
  cancelled: "Cancelled",
};

/**
 * One line of the status timeline.
 *
 * Keyed by the status an event *arrived* at, because that is the step a customer is following — the
 * status it left is what came before it in the list, so repeating it would read as two movements.
 */
export function eventLabel(toStatus: string): string {
  return EVENT_LABELS[toStatus as OrderStatus] ?? `Moved to ${toStatus}`;
}

/**
 * A date, in the reader's own locale and time zone.
 *
 * Only ever rendered after mount. The access token lives in memory (`ADR-0009`), so every screen that
 * shows one of these paints its restoring state first and no date reaches the prerender — which is
 * also what stops a date rendered on the server and the same date rendered in the browser from
 * disagreeing about which day it was.
 */
export function formatDate(value: string): string {
  return new Intl.DateTimeFormat("en-US", { dateStyle: "medium" }).format(new Date(value));
}
