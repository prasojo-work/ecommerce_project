import type { ReactNode } from "react";

import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AuthProvider, useAuth } from "@/lib/auth";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

function wrapper({ children }: { children: ReactNode }) {
  return <AuthProvider>{children}</AuthProvider>;
}

describe("AuthProvider", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("starts signed out when the refresh cookie is missing", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("", { status: 401 })));

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => expect(result.current.ready).toBe(true));
    expect(result.current.user).toBeNull();
  });

  it("signs in and loads the current user", async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/auth/refresh")) return Promise.resolve(new Response("", { status: 401 }));
      if (url.endsWith("/auth/login")) {
        return Promise.resolve(
          jsonResponse({ access_token: "abc", token_type: "Bearer", expires_in: 900 }),
        );
      }
      if (url.endsWith("/auth/me")) {
        return Promise.resolve(
          jsonResponse({ id: 1, email: "shopper@example.com", full_name: "Shopper" }),
        );
      }
      return Promise.resolve(new Response("", { status: 404 }));
    });
    vi.stubGlobal("fetch", fetchMock);

    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.ready).toBe(true));

    await act(async () => {
      await result.current.login("shopper@example.com", "secret-pass-123");
    });

    expect(result.current.user?.email).toBe("shopper@example.com");
    expect(result.current.accessToken).toBe("abc");
  });
});
