import type { ReactNode } from "react";

import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AuthProvider, useAuth } from "@/lib/auth";

const SESSION_HINT_KEY = "nordvik.session";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

const tokens = { access_token: "abc", token_type: "Bearer", expires_in: 900 };
const currentUser = { id: 1, email: "shopper@example.com", full_name: "Shopper" };

/** A fetch stub keyed by URL suffix, so a test names only the routes it cares about. */
function routes(handlers: Record<string, () => Response | Promise<Response>> = {}) {
  return vi.fn((input: RequestInfo | URL) => {
    const url = String(input);
    for (const [suffix, handler] of Object.entries(handlers)) {
      if (url.endsWith(suffix)) {
        return Promise.resolve(handler());
      }
    }
    return Promise.resolve(new Response("", { status: 404 }));
  });
}

function wrapper({ children }: { children: ReactNode }) {
  return <AuthProvider>{children}</AuthProvider>;
}

describe("AuthProvider", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("asks the API about a session when it has never asked this browser", async () => {
    const fetchMock = routes({ "/auth/refresh": () => new Response(null, { status: 204 }) });
    vi.stubGlobal("fetch", fetchMock);

    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.ready).toBe(true));

    expect(result.current.user).toBeNull();
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/auth/refresh"),
      expect.anything(),
    );
  });

  it("skips the request once this browser has reported no session", async () => {
    window.localStorage.setItem(SESSION_HINT_KEY, "0");
    const fetchMock = routes();
    vi.stubGlobal("fetch", fetchMock);

    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.ready).toBe(true));

    expect(result.current.user).toBeNull();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("records the no-session answer so later loads stay quiet", async () => {
    vi.stubGlobal(
      "fetch",
      routes({ "/auth/refresh": () => new Response(null, { status: 204 }) }),
    );

    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.ready).toBe(true));

    expect(window.localStorage.getItem(SESSION_HINT_KEY)).toBe("0");
  });

  it("clears the hint when the API rejects the stored session", async () => {
    window.localStorage.setItem(SESSION_HINT_KEY, "1");
    vi.stubGlobal(
      "fetch",
      routes({ "/auth/refresh": () => new Response(null, { status: 401 }) }),
    );

    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.ready).toBe(true));

    expect(result.current.user).toBeNull();
    expect(window.localStorage.getItem(SESSION_HINT_KEY)).toBe("0");
  });

  it("keeps the hint when the failure is not a 401", async () => {
    window.localStorage.setItem(SESSION_HINT_KEY, "1");
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));

    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.ready).toBe(true));

    expect(window.localStorage.getItem(SESSION_HINT_KEY)).toBe("1");
  });

  it("restores the session when the browser has one", async () => {
    window.localStorage.setItem(SESSION_HINT_KEY, "1");
    vi.stubGlobal(
      "fetch",
      routes({
        "/auth/refresh": () => jsonResponse(tokens),
        "/auth/me": () => jsonResponse(currentUser),
      }),
    );

    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.ready).toBe(true));

    expect(result.current.user?.email).toBe("shopper@example.com");
    expect(result.current.accessToken).toBe("abc");
  });

  it("signs in, loads the current user, and remembers the session", async () => {
    vi.stubGlobal(
      "fetch",
      routes({
        "/auth/refresh": () => new Response(null, { status: 204 }),
        "/auth/login": () => jsonResponse(tokens),
        "/auth/me": () => jsonResponse(currentUser),
      }),
    );

    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.ready).toBe(true));

    await act(async () => {
      await result.current.login("shopper@example.com", "secret-pass-123");
    });

    expect(result.current.user?.email).toBe("shopper@example.com");
    expect(result.current.accessToken).toBe("abc");
    expect(window.localStorage.getItem(SESSION_HINT_KEY)).toBe("1");
  });

  it("forgets the session on logout", async () => {
    window.localStorage.setItem(SESSION_HINT_KEY, "1");
    vi.stubGlobal(
      "fetch",
      routes({
        "/auth/refresh": () => jsonResponse(tokens),
        "/auth/me": () => jsonResponse(currentUser),
        "/auth/logout": () => new Response(null, { status: 204 }),
      }),
    );

    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.ready).toBe(true));

    await act(async () => {
      await result.current.logout();
    });

    expect(result.current.user).toBeNull();
    expect(window.localStorage.getItem(SESSION_HINT_KEY)).toBe("0");
  });
});
