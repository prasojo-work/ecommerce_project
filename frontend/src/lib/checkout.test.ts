import { describe, expect, it } from "vitest";

import type { Quote } from "@/api/checkout";

import { emptyValues } from "./address-form";
import {
  addressPayload,
  defaultMethodCode,
  needsSettlement,
  newIdempotencyKey,
  nextStep,
  optionFor,
  postalLine,
  previousStep,
  STEP_COUNT,
  stepNumber,
} from "./checkout";

const QUOTE: Quote = {
  item_count: 2,
  subtotal: { amount_cents: 24000, currency: "USD" },
  shipping_options: [
    {
      code: "standard",
      name: "Standard",
      description: "Three to five working days.",
      price: { amount_cents: 1900, currency: "USD" },
      total: { amount_cents: 25900, currency: "USD" },
    },
    {
      code: "express",
      name: "Express",
      description: "Next working day.",
      price: { amount_cents: 4500, currency: "USD" },
      total: { amount_cents: 28500, currency: "USD" },
    },
  ],
};

describe("the checkout's order", () => {
  it("numbers the three steps the customer fills in, one-based", () => {
    expect(stepNumber("address")).toBe(1);
    expect(stepNumber("shipping")).toBe(2);
    expect(stepNumber("payment")).toBe(3);
  });

  it("does not count the confirmation as a step to fill in", () => {
    // `stepNumber` still has to answer for it — the confirmation is a step of the flow — but
    // `STEP_COUNT` is what an indicator says "of", and a fourth number there would promise a form.
    expect(stepNumber("done")).toBe(4);
    expect(STEP_COUNT).toBe(3);
  });

  it("walks forward through the steps and stops at the end", () => {
    expect(nextStep("address")).toBe("shipping");
    expect(nextStep("shipping")).toBe("payment");
    expect(nextStep("payment")).toBe("done");
    expect(nextStep("done")).toBeNull();
  });

  it("walks back and stops at the beginning, rather than wrapping", () => {
    expect(previousStep("done")).toBe("payment");
    expect(previousStep("payment")).toBe("shipping");
    expect(previousStep("shipping")).toBe("address");
    expect(previousStep("address")).toBeNull();
  });
});

describe("the address a checkout sends", () => {
  it("drops the label and the default flag, which a checkout has no opinion about", () => {
    const payload = addressPayload({
      ...emptyValues(),
      label: "Home",
      recipient: "Ada Lovelace",
      line1: "12 Analytical Way",
      city: "London",
      postalCode: "EC1A 1BB",
      country: "gb",
      isDefault: true,
    });

    expect(payload).toEqual({
      recipient: "Ada Lovelace",
      line1: "12 Analytical Way",
      line2: "",
      city: "London",
      region: "",
      postal_code: "EC1A 1BB",
      country: "GB",
      phone: "",
    });
    expect("label" in payload).toBe(false);
    expect("is_default" in payload).toBe(false);
  });

  it("trims what the customer typed and upper-cases the country, as the address book does", () => {
    // The same rules rather than a second copy of them: `QuoteAddressSchema` bounds the country to
    // two characters, and a checkout that sent ` us ` would be refused for a reason the address book
    // would never have produced.
    const payload = addressPayload({
      ...emptyValues(),
      recipient: "  Ada Lovelace  ",
      line1: " 12 Analytical Way ",
      city: " London ",
      postalCode: " EC1A 1BB ",
      country: "us",
    });

    expect(payload.recipient).toBe("Ada Lovelace");
    expect(payload.line1).toBe("12 Analytical Way");
    expect(payload.city).toBe("London");
    expect(payload.postal_code).toBe("EC1A 1BB");
    expect(payload.country).toBe("US");
  });
});

describe("reading a quote", () => {
  it("finds the option a code names", () => {
    expect(optionFor(QUOTE, "express")?.total.amount_cents).toBe(28500);
  });

  it("answers nothing for a code the quote does not offer", () => {
    // Not a default and not a fallback: a method the quote never offered has no price, and a made-up
    // one would be a number this app invented (`API.md` section 1).
    expect(optionFor(QUOTE, "drone")).toBeUndefined();
  });

  it("preselects the first option the API returned", () => {
    expect(defaultMethodCode(QUOTE)).toBe("standard");
  });

  it("answers an empty code for a quote with no options, so the continue stays disabled", () => {
    expect(defaultMethodCode({ ...QUOTE, shipping_options: [] })).toBe("");
  });
});

describe("the postal line", () => {
  const ADDRESS = {
    recipient: "Ada Lovelace",
    line1: "12 Analytical Way",
    line2: "",
    city: "London",
    region: "",
    postal_code: "EC1A 1BB",
    country: "GB",
  };

  it("leads with the recipient, unlike an address-book card that leads with its label", () => {
    expect(postalLine(ADDRESS).startsWith("Ada Lovelace")).toBe(true);
  });

  it("drops the optional parts rather than leaving gaps in the middle of the address", () => {
    expect(postalLine(ADDRESS)).toBe("Ada Lovelace, 12 Analytical Way, London, EC1A 1BB, GB");
  });

  it("keeps a second line and a region when the customer gave them", () => {
    expect(postalLine({ ...ADDRESS, line2: "Flat 3", region: "Greater London" })).toBe(
      "Ada Lovelace, 12 Analytical Way, Flat 3, London, Greater London, EC1A 1BB, GB",
    );
  });
});

describe("whether an order still needs settling", () => {
  it("is true only for a pending order", () => {
    expect(needsSettlement({ status: "pending" })).toBe(true);
  });

  it("is false for an order a lost response already settled", () => {
    // The case the retry walks into: the first attempt's *response* was lost, so the order exists and
    // may already be paid for. Settling it again is a 409 the customer would read as a failure for an
    // order they own, so the order's own status decides.
    expect(needsSettlement({ status: "paid" })).toBe(false);
    expect(needsSettlement({ status: "cancelled" })).toBe(false);
  });
});

describe("the idempotency key", () => {
  it("is a fresh key each time, so two tabs checking out cannot share one", () => {
    const first = newIdempotencyKey();
    expect(first).not.toBe(newIdempotencyKey());
    expect(first).toMatch(/^[0-9a-f-]{36}$/);
  });
});
