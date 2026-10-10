import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// `unstable_rethrow` comes from `next/navigation`, which expects a Next server context. Replacing
// it keeps this module loadable in the node test environment; the rethrow itself is framework
// behaviour, not ours to assert on.
vi.mock("next/navigation", () => ({ unstable_rethrow: () => undefined }));

const { fetchProduct } = await import("./client");

const PRODUCT = {
  id: 1,
  slug: "oak-chair",
  name: "Oak Chair",
  description: "A chair.",
  category: { slug: "seating", name: "Seating" },
  price: { amount_cents: 24000, currency: "USD" },
  material: "Oak",
  color: "Natural",
  width_cm: null,
  height_cm: null,
  depth_cm: null,
  images: [],
  variants: [],
  availability: { in_stock: true, in_stock_variants: 1 },
};

function respondWith(body: unknown, status = 200) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => {
      return new Response(JSON.stringify(body), {
        status,
        headers: { "content-type": "application/json" },
      });
    }),
  );
}

beforeEach(() => {
  // The failure paths log deliberately, for the operator rather than the visitor. Silence it so a
  // passing run stays readable.
  vi.spyOn(console, "error").mockImplementation(() => undefined);
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("fetchProduct", () => {
  it("returns the product the API serves", async () => {
    respondWith(PRODUCT);

    await expect(fetchProduct("oak-chair")).resolves.toEqual({ ok: true, product: PRODUCT });
  });

  it("reports an unknown slug as not-found, so the page can return a real 404", async () => {
    respondWith({ detail: "No product with slug 'nope'." }, 404);

    await expect(fetchProduct("nope")).resolves.toEqual({ ok: false, kind: "not-found" });
  });

  it("reports a service failure as unavailable, not as a missing product", async () => {
    respondWith({}, 503);

    const result = await fetchProduct("oak-chair");

    // The message pins which path produced this: an answered request, not a failed one.
    expect(result).toEqual({
      ok: false,
      kind: "unavailable",
      message: expect.stringContaining("having trouble"),
    });
  });

  it("reports a transport failure as unavailable rather than throwing", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new TypeError("fetch failed");
      }),
    );

    const result = await fetchProduct("oak-chair");

    expect(result).toEqual({ ok: false, kind: "unavailable", message: expect.any(String) });
  });
});
