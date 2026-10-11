import createClient from "openapi-fetch";

import { asFailure, type ApiFailure } from "@/lib/api-failure";
import { getApiBaseUrl } from "@/lib/config";
import {
  clearSession,
  createSessionClient,
  getSession,
  setSession,
  type Session,
} from "@/lib/session";

import type { paths } from "./schema";

/**
 * The auth wire: one function per endpoint, each of which leaves the session correct.
 *
 * Nothing here decides what the customer sees. Failures come back as values rather than exceptions
 * — the same choice the catalog client makes — because a wrong password is an ordinary outcome of a
 * form, not an error that should reach an error boundary and take the page with it.
 */

const client = createClient<paths>({
  baseUrl: getApiBaseUrl(),
  // Resolved on every call rather than captured once, for the reason `client.ts` spells out: Next
  // replaces the global `fetch`, and a reference taken at import time can predate that.
  fetch: (request) => fetch(request),
});

/** The refresh cookie is scoped to `/api/v1/auth`, so every call here must be allowed to send it. */
const WITH_COOKIE = { credentials: "include" } as const;

/** The envelope as this module's callers see it. Reading it is `lib/api-failure.ts`'s job. */
export type AuthFailure = ApiFailure;

export type AuthSuccess = { ok: true; session: Session };

export type AuthOutcome = AuthSuccess | AuthFailure;

function established(session: Session): AuthSuccess {
  setSession(session);
  return { ok: true, session };
}

export async function login(email: string, password: string): Promise<AuthOutcome> {
  const { data, error, response } = await client.POST("/api/v1/auth/login", {
    ...WITH_COOKIE,
    body: { email, password },
  });

  return data
    ? established({ accessToken: data.access_token, user: data.user })
    : asFailure(error, response);
}

export async function register(
  email: string,
  password: string,
  displayName: string,
): Promise<AuthOutcome> {
  const { data, error, response } = await client.POST("/api/v1/auth/register", {
    ...WITH_COOKIE,
    body: { email, password, display_name: displayName },
  });

  return data
    ? established({ accessToken: data.access_token, user: data.user })
    : asFailure(error, response);
}

/**
 * Exchange the refresh cookie for a new access token.
 *
 * Anything but a new pair is the end of the session — the cookie is missing, expired, or has
 * already been used and revoked — so the store is emptied rather than left holding a token the API
 * has stopped accepting.
 */
async function renewFromCookie(): Promise<Session | null> {
  const { data } = await client.POST("/api/v1/auth/refresh", { ...WITH_COOKIE });
  if (!data) {
    clearSession();
    return null;
  }

  const session = { accessToken: data.access_token, user: data.user };
  setSession(session);
  return session;
}

const sessionClient = createSessionClient({
  refresh: renewFromCookie,
  fetch: (input, init) => fetch(input, init),
});

/** A protected call, retried once against a fresh token. See `lib/session.ts` for the guard. */
export function authorizedFetch(input: string, init?: RequestInit): Promise<Response> {
  return sessionClient.authorizedFetch(input, init);
}

/** Restore (or confirm the absence of) a session — the app's silent refresh. */
export function renewSession(): Promise<Session | null> {
  return sessionClient.renew();
}

/**
 * End the session (`US-2.3`).
 *
 * The API is told first, because `ADR-0009` requires logout to invalidate the refresh token
 * *server-side* rather than only forgetting it in the browser. The local store is cleared either
 * way: a logout that failed because the token was already dead has still logged the user out, and
 * leaving a session behind would show a signed-in header over an API that refuses every call.
 */
export async function logout(): Promise<void> {
  const token = getSession()?.accessToken ?? null;
  try {
    await client.POST("/api/v1/auth/logout", {
      ...WITH_COOKIE,
      headers: token === null ? undefined : { Authorization: `Bearer ${token}` },
    });
  } finally {
    clearSession();
  }
}
