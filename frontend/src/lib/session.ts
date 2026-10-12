import type { components } from "@/api/schema";

/**
 * The session, and the one rule that keeps it alive (`ADR-0009`, `US-2.3`).
 *
 * The access token lives here — in a module variable, which is memory in the tab — and nowhere else.
 * It is never written to `localStorage` or `sessionStorage`, because anything a script can read, an
 * injected script can read, and that is exactly what `ADR-0009` rejected. The consequence is that a
 * reload loses it, which is why the token's absence is not the same as "signed out": the refresh
 * cookie is still there, so the app asks for a new access token on load.
 */

export type SessionUser = components["schemas"]["UserSchema"];

export type Session = {
  accessToken: string;
  user: SessionUser;
};

let current: Session | null = null;
const listeners = new Set<() => void>();

/** The live session, or `null`. Reads are snapshots: the object is replaced, never mutated. */
export function getSession(): Session | null {
  return current;
}

/**
 * React reads through this via `useSyncExternalStore`, so a sign-in or sign-out re-renders whatever
 * is showing the account without any state being duplicated into a component.
 */
export function subscribeToSession(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function setSession(session: Session): void {
  current = session;
  for (const listener of listeners) listener();
}

/**
 * Forget the tokens. The caller is responsible for telling the API as well (`logout`), because this
 * is also the path taken when the API has already rejected the session — there is nothing left to
 * revoke, and asking would only produce another refusal.
 */
export function clearSession(): void {
  current = null;
  for (const listener of listeners) listener();
}

export type SessionClient = {
  /**
   * Make an authenticated request, renewing the access token once if the API rejects it.
   *
   * `credentials: "include"` is deliberate even though this uses a bearer token: the refresh token
   * is an httpOnly cookie scoped to the auth routes, so it only travels if the request asks for it
   * — and a renewal without it would renew nothing. (`ADR-0008`'s guest cart cookie was once the
   * other reason to send it; `ADR-0017` dropped the guest cart, and the refresh cookie remains.)
   */
  authorizedFetch(input: string, init?: RequestInit): Promise<Response>;

  /**
   * Renew the access token from the refresh cookie, or `null` if there is no session to renew.
   *
   * Exposed because the app's restore-on-load must share the same single-flight gate as every
   * retry below. Paging in the whole app is not the only thing that can race: a reload that renews
   * while a request is already being retried is the same collision, one page-load earlier.
   */
  renew(): Promise<Session | null>;
};

export function createSessionClient(deps: {
  /** Obtain a new access token from the refresh cookie. Returns `null` if there is no session left. */
  refresh: () => Promise<Session | null>;
  fetch: (input: string, init?: RequestInit) => Promise<Response>;
}): SessionClient {
  let inFlight: Promise<Session | null> | null = null;

  /**
   * One refresh at a time, for everyone.
   *
   * This is a correctness guard, not a cache. The API rotates the refresh token and treats a second
   * use of an already-used one as evidence that a copy is in circulation — it then revokes *every*
   * session for that account (`accounts/tokens.py`). So if two protected requests were to 401 at the
   * same moment, two refreshes would race, the loser would look like a thief, and the user would be
   * signed out of everything. Two tabs are enough to trigger it; one page making two calls at once
   * is enough. Everything waiting on the same refresh shares this promise.
   */
  function refreshOnce(): Promise<Session | null> {
    if (inFlight === null) {
      inFlight = deps.refresh().finally(() => {
        inFlight = null;
      });
    }
    return inFlight;
  }

  function attempt(input: string, init: RequestInit | undefined, token: string | null) {
    const headers = new Headers(init?.headers);
    if (token !== null) {
      headers.set("Authorization", `Bearer ${token}`);
    }
    return deps.fetch(input, { ...init, headers, credentials: "include" });
  }

  return {
    renew: refreshOnce,

    async authorizedFetch(input, init) {
      const first = await attempt(input, init, getSession()?.accessToken ?? null);
      if (first.status !== 401) {
        return first;
      }

      const renewed = await refreshOnce();
      if (renewed === null) {
        // No session to recover. The 401 is the honest answer, and the caller decides what the
        // customer sees; there is nothing here worth retrying.
        return first;
      }

      // Exactly one retry: if the fresh token is refused too, the problem is not staleness, and
      // looping would turn a broken session into a request storm.
      return attempt(input, init, renewed.accessToken);
    },
  };
}
