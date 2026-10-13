import { asFailure, type ApiFailure } from "@/lib/api-failure";

import type { components } from "./schema";
import { createAuthorizedClient } from "./transport";

/**
 * The checkout wire (`API.md` sections 6 and 7, `US-4.1`-`US-4.4`).
 *
 * Three calls in an order that matters: quote the cart, place the order, settle the payment. Each one
 * answers with the state the next one needs, and nothing is recomputed here — the subtotal, the
 * shipping price and the total are the API's arithmetic (`API.md` section 1), because a client that
 * added them up itself would be a second implementation of a rule that has to agree to the cent.
 *
 * All three need a bearer token, so `authorizedFetch` is the transport, and all three return failures
 * as values rather than throwing: a declined card is an ordinary outcome of this screen, not
 * something that should reach an error boundary and take the checkout with it.
 */

export type Quote = components["schemas"]["QuoteSchema"];
export type ShippingOption = components["schemas"]["ShippingOptionSchema"];
export type QuoteRequest = components["schemas"]["QuoteRequestSchema"];
export type Order = components["schemas"]["OrderSchema"];
export type OrderLine = components["schemas"]["OrderItemSchema"];
export type OrderCreatePayload = components["schemas"]["OrderCreateSchema"];
export type Settlement = components["schemas"]["MockPaymentResultSchema"];

export type QuoteOutcome = { ok: true; quote: Quote } | ApiFailure;

/**
 * A placed order, and whether the API made it now or recognised the key it was given.
 *
 * The distinction is carried out of here rather than thrown away because it changes what the screen
 * may do next: a replay is an order that already exists, and it may already have been paid for.
 */
export type OrderOutcome = { ok: true; order: Order; replayed: boolean } | ApiFailure;

export type SettlementOutcome = { ok: true; settlement: Settlement } | ApiFailure;

/** Which way the mock provider should answer (`ADR-0010`). */
export type SettlementAttempt = "capture" | "decline";

const client = createAuthorizedClient();

/**
 * `US-4.2`: the cart's subtotal plus every shipping option **with the total it produces**.
 *
 * Reading the quote is also the first thing that can refuse the address (`US-4.1`), which is why the
 * screen asks for it when an address is chosen rather than when the order is placed: the refusal
 * belongs beside the address, not at the end of a checkout.
 */
export async function fetchQuote(payload: QuoteRequest): Promise<QuoteOutcome> {
  const { data, error, response } = await client.POST("/api/v1/checkout/quote", { body: payload });

  if (!response.ok || data === undefined) {
    return asFailure(error, response);
  }

  return { ok: true, quote: data };
}

/**
 * `US-4.3`, first half: turn the cart into an order, reserving its stock.
 *
 * `idempotencyKey` is the whole reason a retry is safe. The order is created inside one transaction
 * that also decrements stock (`ADR-0017`), so a second attempt after a lost response would reserve a
 * second time — instead the API answers `200` with the order the first attempt made. The key belongs
 * to the *attempt*, not to the click: a fresh one per click would defeat exactly this.
 */
export async function placeOrder(
  payload: OrderCreatePayload,
  idempotencyKey: string,
): Promise<OrderOutcome> {
  const { data, error, response } = await client.POST("/api/v1/orders", {
    params: { header: { "Idempotency-Key": idempotencyKey } },
    body: payload,
  });

  if (!response.ok || data === undefined) {
    return asFailure(error, response);
  }

  // `201` is an order this call created; `200` is the key being recognised. Both carry the order.
  return { ok: true, order: data, replayed: response.status === 200 };
}

/**
 * `US-4.3`, second half: settle the payment and let it decide the order's fate.
 *
 * The capture decides, not the caller — `confirm` moves the order to `paid` and `fail` cancels it,
 * returning the stock the order reserved. The result carries the order's status for the same reason:
 * the screen should read the outcome from the order rather than infer one from a payment.
 */
export async function settlePayment(
  orderNumber: string,
  attempt: SettlementAttempt,
): Promise<SettlementOutcome> {
  const body = { order_number: orderNumber };

  const { data, error, response } =
    attempt === "capture"
      ? await client.POST("/api/v1/payments/mock/confirm", { body })
      : await client.POST("/api/v1/payments/mock/fail", { body });

  if (!response.ok || data === undefined) {
    return asFailure(error, response);
  }

  return { ok: true, settlement: data };
}
