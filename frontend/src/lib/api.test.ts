// @vitest-environment node

import { afterEach, describe, expect, it, vi } from "vitest";

import { fetchProduct, fetchProducts } from "@/lib/api";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

describe("api client", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("builds the products query string from the filters", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse({ count: 0, page: 1, page_size: 12, results: [] }));

    await fetchProducts({ q: "sofa", category: "living-room", sort: "price", page: 2 });

    expect(fetchMock).toHaveBeenCalledOnce();
    const url = String(fetchMock.mock.calls[0][0]);
    expect(url).toContain("/products?");
    expect(url).toContain("q=sofa");
    expect(url).toContain("category=living-room");
    expect(url).toContain("sort=price");
    expect(url).toContain("page=2");
  });

  it("omits the query string when there are no filters", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse({ count: 0, page: 1, page_size: 12, results: [] }));

    await fetchProducts();

    expect(String(fetchMock.mock.calls[0][0])).toMatch(/\/products$/);
  });

  it("returns null for a missing product", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response("", { status: 404 }));
    await expect(fetchProduct("missing")).resolves.toBeNull();
  });

  it("throws on a server error", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response("", { status: 500 }));
    await expect(fetchProducts()).rejects.toThrow();
  });
});
