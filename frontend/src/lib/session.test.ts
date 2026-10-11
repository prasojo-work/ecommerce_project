import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  clearSession,
  createSessionClient,
  getSession,
  setSession,
  subscribeToSession,
} from "./session";

const ada = { id: 1, email: "ada@example.com", display_name: "Ada", is_staff: false };

function response(status: number): Response {
  return new Response(JSON.stringify({}), {
    status,
    headers: { "content-type": "application/json" },
  });
}

/** A fetch that records what it was asked, so the assertions can be about the request itself. */
function recordingFetch(reply: (authorization: string | null) => Response) {
  const calls: Array<{ url: string; init: RequestInit | undefined }> = [];
  const fetch = vi.fn(async (url: string, init?: RequestInit) => {
    calls.push({ url, init });
    return reply(new Headers(init?.headers).get("Authorization"));
  });
  return { fetch, calls };
}

function authorizationOf(call: { init: RequestInit | undefined }): string | null {
  return new Headers(call.init?.headers).get("Authorization");
}

describe("the session store", () => {
  beforeEach(() => clearSession());

  it("starts with no session", () => {
    expect(getSession()).toBeNull();
  });

  it("hands back what was set", () => {
    setSession({ accessToken: "token-1", user: ada });

    expect(getSession()).toEqual({ accessToken: "token-1", user: ada });
  });

  it("tells subscribers when it changes, and stops when they leave", () => {
    const listener = vi.fn();
    const unsubscribe = subscribeToSession(listener);

    setSession({ accessToken: "token-1", user: ada });
    expect(listener).toHaveBeenCalledTimes(1);

    unsubscribe();
    clearSession();
    expect(listener).toHaveBeenCalledTimes(1);
  });
});

describe("authorizedFetch", () => {
  beforeEach(() => clearSession());

  it("sends the access token as a bearer header", async () => {
    setSession({ accessToken: "token-1", user: ada });
    const { fetch, calls } = recordingFetch(() => response(200));
    const client = createSessionClient({ fetch, refresh: vi.fn() });

    await client.authorizedFetch("/api/v1/auth/me");

    expect(authorizationOf(calls[0])).toBe("Bearer token-1");
  });

  it("sends no authorization header when there is no session", async () => {
    const { fetch, calls } = recordingFetch(() => response(200));
    const client = createSessionClient({ fetch, refresh: vi.fn() });

    await client.authorizedFetch("/api/v1/products");

    expect(authorizationOf(calls[0])).toBeNull();
  });

  it("allows credentials, so the guest cart cookie travels with the call", async () => {
    const { fetch, calls } = recordingFetch(() => response(200));
    const client = createSessionClient({ fetch, refresh: vi.fn() });

    await client.authorizedFetch("/api/v1/products");

    expect(calls[0].init?.credentials).toBe("include");
  });

  it("passes a successful response straight through without refreshing", async () => {
    setSession({ accessToken: "token-1", user: ada });
    const { fetch } = recordingFetch(() => response(200));
    const refresh = vi.fn();
    const client = createSessionClient({ fetch, refresh });

    const result = await client.authorizedFetch("/api/v1/auth/me");

    expect(result.status).toBe(200);
    expect(refresh).not.toHaveBeenCalled();
  });

  it("refreshes once and retries when the access token has expired", async () => {
    setSession({ accessToken: "expired", user: ada });
    const { fetch, calls } = recordingFetch((authorization) =>
      authorization === "Bearer fresh" ? response(200) : response(401),
    );
    const refresh = vi.fn(async () => ({ accessToken: "fresh", user: ada }));
    const client = createSessionClient({ fetch, refresh });

    const result = await client.authorizedFetch("/api/v1/auth/me");

    expect(result.status).toBe(200);
    expect(refresh).toHaveBeenCalledTimes(1);
    expect(authorizationOf(calls[1])).toBe("Bearer fresh");
  });

  it("refreshes once when two calls are refused at the same moment", async () => {
    // The bug this prevents is not a wasted request. The API rotates refresh tokens and treats a
    // second use of an old one as theft, revoking every session for the account — so a page that
    // makes two protected calls at once would sign the customer out of everything.
    setSession({ accessToken: "expired", user: ada });
    const { fetch } = recordingFetch((authorization) =>
      authorization === "Bearer fresh" ? response(200) : response(401),
    );
    let resolveRefresh: ((session: { accessToken: string; user: typeof ada }) => void) | undefined;
    const refresh = vi.fn(
      () =>
        new Promise<{ accessToken: string; user: typeof ada }>((resolve) => {
          resolveRefresh = resolve;
        }),
    );
    const client = createSessionClient({ fetch, refresh });

    const both = Promise.all([
      client.authorizedFetch("/api/v1/auth/me"),
      client.authorizedFetch("/api/v1/auth/me"),
    ]);
    await vi.waitFor(() => expect(refresh).toHaveBeenCalled());
    resolveRefresh?.({ accessToken: "fresh", user: ada });
    const [first, second] = await both;

    expect(refresh).toHaveBeenCalledTimes(1);
    expect(first.status).toBe(200);
    expect(second.status).toBe(200);
  });

  it("shares one refresh between a restore and a rejected request", async () => {
    // The same collision, reached the way a page actually loads: the restore-on-mount is still
    // waiting on its refresh while a protected call is refused. The refresh is held open on purpose
    // — a mock that resolves immediately lets the restore finish before the request is even
    // refused, and the browser cannot produce that sequence, because the refresh it makes is a
    // network call. Getting this wrong is how the first version of this test passed a wrong
    // assumption.
    setSession({ accessToken: "expired", user: ada });
    const { fetch } = recordingFetch((authorization) =>
      authorization === "Bearer fresh" ? response(200) : response(401),
    );
    let resolveRefresh: ((session: { accessToken: string; user: typeof ada }) => void) | undefined;
    const refresh = vi.fn(
      () =>
        new Promise<{ accessToken: string; user: typeof ada }>((resolve) => {
          resolveRefresh = resolve;
        }),
    );
    const client = createSessionClient({ fetch, refresh });

    const restoring = client.renew();
    const retried = client.authorizedFetch("/api/v1/auth/me");
    await vi.waitFor(() => expect(fetch).toHaveBeenCalled());
    resolveRefresh?.({ accessToken: "fresh", user: ada });
    const [restored, call] = await Promise.all([restoring, retried]);

    expect(refresh).toHaveBeenCalledTimes(1);
    expect(restored?.accessToken).toBe("fresh");
    expect(call.status).toBe(200);
  });

  it("surfaces the 401 when the refresh cannot restore a session", async () => {
    setSession({ accessToken: "expired", user: ada });
    const { fetch } = recordingFetch(() => response(401));
    const refresh = vi.fn(async () => null);
    const client = createSessionClient({ fetch, refresh });

    const result = await client.authorizedFetch("/api/v1/auth/me");

    expect(result.status).toBe(401);
    expect(refresh).toHaveBeenCalledTimes(1);
    expect(fetch).toHaveBeenCalledTimes(1);
  });

  it("does not loop when the refreshed token is refused too", async () => {
    setSession({ accessToken: "expired", user: ada });
    const { fetch } = recordingFetch(() => response(401));
    const refresh = vi.fn(async () => ({ accessToken: "still-refused", user: ada }));
    const client = createSessionClient({ fetch, refresh });

    const result = await client.authorizedFetch("/api/v1/auth/me");

    expect(result.status).toBe(401);
    expect(refresh).toHaveBeenCalledTimes(1);
    expect(fetch).toHaveBeenCalledTimes(2);
  });
});
