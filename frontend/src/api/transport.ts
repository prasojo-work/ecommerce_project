import createClient from "openapi-fetch";

import { authorizedFetch } from "@/api/auth";
import { getApiBaseUrl } from "@/lib/config";

import type { paths } from "./schema";

/**
 * The transport the authenticated API modules share.
 *
 * The adapter below is small, and it is the kind of small that fails *silently* when it is rewritten
 * by hand — so it exists once. `api/account.ts`, `api/cart.ts`, `api/checkout.ts` and `api/orders.ts`
 * each call `createAuthorizedClient()` and none of them owns the details.
 */

/**
 * Hand openapi-fetch's request to `authorizedFetch`.
 *
 * Two details, both of which produce a silent failure rather than an error:
 *
 * - **A `Request` is not spreadable.** `{ ...request }` yields an empty object, so the method and the
 *   body would be dropped and every `POST` would arrive as a bodiless `GET`-shaped request. The parts
 *   are copied explicitly instead.
 * - **The body is read to text rather than streamed.** `authorizedFetch` retries once after renewing
 *   the token, and a stream can only be read once — a streamed body would make the retry send
 *   nothing at all, so a call that collided with an expired token would fail for the wrong reason.
 */
async function send(request: Request): Promise<Response> {
  const bodiless = request.method === "GET" || request.method === "DELETE";
  return authorizedFetch(request.url, {
    method: request.method,
    headers: request.headers,
    body: bodiless ? undefined : await request.text(),
  });
}

/**
 * A typed client for the routes that need a bearer token (`ADR-0017`).
 *
 * The base URL is resolved on each call rather than captured once for the process, the reason
 * `api/client.ts` gives: Next replaces the global `fetch`, and a reference taken at import time can
 * predate that replacement.
 */
export function createAuthorizedClient() {
  return createClient<paths>({ baseUrl: getApiBaseUrl(), fetch: send });
}
