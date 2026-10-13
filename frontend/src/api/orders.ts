import { asFailure, type ApiFailure } from "@/lib/api-failure";

import type { components } from "./schema";
import { createAuthorizedClient } from "./transport";

/**
 * The order history and order detail routes (`API.md` section 6, `US-4.5`, `US-4.6`).
 *
 * Both read the caller's *own* orders, and that scoping is the API's rather than a filter applied
 * here: an order belonging to somebody else is a `404`, not a row this module hides. Both also return
 * failures as values, the choice every client here makes — a missing order is an ordinary page state,
 * not something that should reach an error boundary and take the route with it.
 */

export type OrderSummary = components["schemas"]["OrderSummarySchema"];
export type OrderPage = components["schemas"]["OrderPageSchema"];
export type OrderDetail = components["schemas"]["OrderDetailSchema"];

export type HistoryOutcome = { ok: true; page: OrderPage } | ApiFailure;
export type DetailOutcome = { ok: true; order: OrderDetail } | ApiFailure;

const client = createAuthorizedClient();

/**
 * One page of the caller's orders, newest first (`US-4.5`).
 *
 * `page_size` is deliberately left to the API's default, unlike the catalog grid. The grid sends it
 * because its skeleton has to reserve exactly as many cards as will arrive, or the page shifts when
 * the data lands; a list of orders has no such shape to guess, and the response carries the size it
 * used, so the pager still knows how many pages there are.
 */
export async function loadOrders(page: number): Promise<HistoryOutcome> {
  const { data, error, response } = await client.GET("/api/v1/orders", {
    params: { query: { page } },
  });

  if (!response.ok || data === undefined) {
    return asFailure(error, response);
  }

  return { ok: true, page: data };
}

/**
 * One order, with the timeline that explains the status it is in (`US-4.6`).
 *
 * A number that is not the caller's answers `404` with the same body as a number that never existed
 * (`orders/api.py`), so there is nothing here to tell apart — and therefore nothing to tell.
 */
export async function loadOrder(orderNumber: string): Promise<DetailOutcome> {
  const { data, error, response } = await client.GET("/api/v1/orders/{order_number}", {
    params: { path: { order_number: orderNumber } },
  });

  if (!response.ok || data === undefined) {
    return asFailure(error, response);
  }

  return { ok: true, order: data };
}
