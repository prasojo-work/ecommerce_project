import createClient from "openapi-fetch";

import { authorizedFetch } from "@/api/auth";
import { asFailure, messageForFailure, type ApiFailure } from "@/lib/api-failure";
import { setCart, setCartFailure, type Cart } from "@/lib/cart";
import { getApiBaseUrl } from "@/lib/config";

import type { paths } from "./schema";

/**
 * The cart's four endpoints (`API.md` section 5, `US-3.1`-`US-3.4`).
 *
 * Every one of them answers with the whole cart, so every one of them writes the store on success.
 * That is what keeps the header's count honest: the response to an add *is* the new count, so
 * nothing is incremented by hand and the two can never drift.
 *
 * All four need a bearer token (`ADR-0017`), so `authorizedFetch` is the transport — which is also
 * what makes a call that collides with an expired access token renew once and retry, instead of
 * surfacing to the customer as a sign-out.
 */

export type CartOutcome = { ok: true; cart: Cart } | ApiFailure;

/** See `api/account.ts`: a `Request` does not spread, and a streamed body cannot be retried. */
async function send(request: Request): Promise<Response> {
  const bodiless = request.method === "GET" || request.method === "DELETE";
  return authorizedFetch(request.url, {
    method: request.method,
    headers: request.headers,
    body: bodiless ? undefined : await request.text(),
  });
}

const client = createClient<paths>({ baseUrl: getApiBaseUrl(), fetch: send });

/**
 * The caller's cart (`US-3.4`), and the read the header's count comes from.
 *
 * A failure leaves the store alone rather than emptying it: a request that could not be made says
 * nothing about what the cart holds, and a badge that dropped to zero on a flaky connection would
 * be a worse lie than a stale number.
 */
export async function loadCart(): Promise<CartOutcome> {
  const { data, error, response } = await client.GET("/api/v1/cart");

  if (!response.ok || data === undefined) {
    const failure = asFailure(error, response);
    // Written to the store as well as returned: the page reads the failure from the same place it
    // reads the cart, so a retry that works clears the message by replacing what it was about.
    setCartFailure(messageForFailure(failure.status, failure.message));
    return failure;
  }

  setCart(data);
  return { ok: true, cart: data };
}

/**
 * `US-3.1`. The default quantity of one is what the product page adds — the colour it shows, once.
 *
 * `409` is the API refusing a quantity above stock, with both numbers in its message (`US-3.2`), and
 * it arrives here as an ordinary failure for the button to display rather than an exception.
 */
export async function addToCart(variantId: number, quantity = 1): Promise<CartOutcome> {
  const { data, error, response } = await client.POST("/api/v1/cart/items", {
    body: { variant_id: variantId, quantity },
  });

  if (!response.ok || data === undefined) {
    return asFailure(error, response);
  }

  setCart(data);
  return { ok: true, cart: data };
}

/** `US-3.2`. The response carries the recomputed totals, so no arithmetic happens here. */
export async function setLineQuantity(lineId: number, quantity: number): Promise<CartOutcome> {
  const { data, error, response } = await client.PATCH("/api/v1/cart/items/{line_id}", {
    params: { path: { line_id: lineId } },
    body: { quantity },
  });

  if (!response.ok || data === undefined) {
    return asFailure(error, response);
  }

  setCart(data);
  return { ok: true, cart: data };
}

/** `US-3.3`. Removal answers with the remaining cart, so the totals it reports are the new ones. */
export async function removeLine(lineId: number): Promise<CartOutcome> {
  const { data, error, response } = await client.DELETE("/api/v1/cart/items/{line_id}", {
    params: { path: { line_id: lineId } },
  });

  if (!response.ok || data === undefined) {
    return asFailure(error, response);
  }

  setCart(data);
  return { ok: true, cart: data };
}
