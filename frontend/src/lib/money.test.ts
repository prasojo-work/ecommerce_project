import { describe, expect, it } from "vitest";

import { formatPrice } from "./money";

describe("formatPrice", () => {
  it("renders the format UX.md section 9 fixes", () => {
    expect(formatPrice({ amount_cents: 124000, currency: "USD" })).toBe("$1,240.00");
  });

  it("keeps the cents rather than rounding them away", () => {
    expect(formatPrice({ amount_cents: 24999, currency: "USD" })).toBe("$249.99");
  });

  it("reads the currency from the payload instead of assuming dollars", () => {
    expect(formatPrice({ amount_cents: 100000, currency: "EUR" })).toContain("€");
  });
});
