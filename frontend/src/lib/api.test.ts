// @vitest-environment node

import { afterEach, describe, expect, it, vi } from "vitest";

import {
  createOrder,
  fetchOrder,
  fetchOrders,
  fetchProduct,
  fetchProducts,
  payWithMock,
} from "@/lib/api";

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

describe("orders api", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("posts the order with the bearer token", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse({ number: "NDV-2026-000001" }, 201));

    await createOrder("token-123", {
      address_id: 7,
      shipping_method: "express",
      idempotency_key: "key-1",
    });

    const [url, init] = fetchMock.mock.calls[0];
    expect(String(url)).toMatch(/\/orders$/);
    expect(init?.method).toBe("POST");
    expect((init?.headers as Record<string, string>).authorization).toBe("Bearer token-123");
    expect(JSON.parse(String(init?.body))).toEqual({
      address_id: 7,
      shipping_method: "express",
      idempotency_key: "key-1",
    });
  });

  it("sends the simulated failure flag to the mock gateway", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse({ status: "failed" }, 201));

    await payWithMock("token-123", "NDV-2026-000001", true);

    const [url, init] = fetchMock.mock.calls[0];
    expect(String(url)).toMatch(/\/payments\/mock$/);
    expect(JSON.parse(String(init?.body))).toEqual({
      order_number: "NDV-2026-000001",
      simulate_failure: true,
    });
  });

  it("loads a single order by number", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse({ number: "NDV-2026-000001" }));

    await fetchOrder("token-123", "NDV-2026-000001");

    expect(String(fetchMock.mock.calls[0][0])).toMatch(/\/orders\/NDV-2026-000001$/);
  });

  it("surfaces the API detail message on failure", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({ detail: "Your cart is empty." }, 400),
    );

    await expect(fetchOrders("token-123")).rejects.toThrow("Your cart is empty.");
  });
});
