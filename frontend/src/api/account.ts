import createClient from "openapi-fetch";

import { authorizedFetch } from "@/api/auth";
import { asFailure, type ApiFailure } from "@/lib/api-failure";
import { getApiBaseUrl } from "@/lib/config";
import { getSession, setSession, type SessionUser } from "@/lib/session";

import type { components, paths } from "./schema";

/**
 * The account's own endpoints (`US-2.4`, `US-2.5`) — the first in the app that need a token, and
 * therefore the first to go through `lib/session.ts`.
 *
 * Failures come back as values rather than exceptions, the same choice `api/auth.ts` and the catalog
 * client make: an address the API refuses is an ordinary outcome of a form, not something that
 * should reach an error boundary and take the page with it.
 */

export type Address = components["schemas"]["AddressSchema"];
export type AddressCreatePayload = components["schemas"]["AddressCreateSchema"];
export type AddressUpdatePayload = components["schemas"]["AddressUpdateSchema"];

export type AddressListOutcome = { ok: true; addresses: Address[] } | ApiFailure;
export type AddressOutcome = { ok: true; address: Address } | ApiFailure;
export type ProfileOutcome = { ok: true; user: SessionUser } | ApiFailure;
export type DeletedOutcome = { ok: true } | ApiFailure;

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

const client = createClient<paths>({ baseUrl: getApiBaseUrl(), fetch: send });

/**
 * `PATCH /auth/me` (`US-2.4`), and the reason it touches the session: the header renders the name
 * from the store, so a rename that did not update it would leave the page saying one thing and the
 * header another until the next reload. There is nothing to merge beyond the user — the access token
 * is unchanged, and a renewal during the call has already written its own.
 */
export async function updateProfile(displayName: string): Promise<ProfileOutcome> {
  const { data, error, response } = await client.PATCH("/api/v1/auth/me", {
    body: { display_name: displayName },
  });

  if (!response.ok || data === undefined) {
    return asFailure(error, response);
  }

  const current = getSession();
  if (current !== null) {
    setSession({ ...current, user: data });
  }

  return { ok: true, user: data };
}

/** The caller's addresses, default first, as `API.md` section 8 promises. */
export async function listAddresses(): Promise<AddressListOutcome> {
  const { data, error, response } = await client.GET("/api/v1/addresses");

  if (!response.ok || data === undefined) {
    return asFailure(error, response);
  }

  return { ok: true, addresses: data };
}

export async function createAddress(payload: AddressCreatePayload): Promise<AddressOutcome> {
  const { data, error, response } = await client.POST("/api/v1/addresses", { body: payload });

  if (!response.ok || data === undefined) {
    return asFailure(error, response);
  }

  return { ok: true, address: data };
}

export async function updateAddress(
  id: number,
  payload: AddressUpdatePayload,
): Promise<AddressOutcome> {
  const { data, error, response } = await client.PATCH("/api/v1/addresses/{address_id}", {
    params: { path: { address_id: id } },
    body: payload,
  });

  if (!response.ok || data === undefined) {
    return asFailure(error, response);
  }

  return { ok: true, address: data };
}

/**
 * `DELETE` answers `204`, so there is no body to read and success is `response.ok` rather than the
 * presence of data — the one place in this module where those two differ.
 */
export async function deleteAddress(id: number): Promise<DeletedOutcome> {
  const { error, response } = await client.DELETE("/api/v1/addresses/{address_id}", {
    params: { path: { address_id: id } },
  });

  if (!response.ok) {
    return asFailure(error, response);
  }

  return { ok: true };
}
