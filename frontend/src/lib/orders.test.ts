import { describe, expect, it } from "vitest";

import {
  formatOrderDate,
  newIdempotencyKey,
  orderStatusLabel,
  orderStatusTone,
} from "@/lib/orders";

describe("order helpers", () => {
  it("maps known statuses to human labels", () => {
    expect(orderStatusLabel("pending_payment")).toBe("Awaiting payment");
    expect(orderStatusLabel("paid")).toBe("Paid");
    expect(orderStatusLabel("shipped")).toBe("Shipped");
  });

  it("falls back to the raw status it does not know", () => {
    expect(orderStatusLabel("refunded")).toBe("refunded");
    expect(orderStatusTone("refunded")).toBe("bg-neutral-200 text-neutral-800");
  });

  it("gives every known status a distinct label", () => {
    const statuses = [
      "pending_payment",
      "paid",
      "processing",
      "shipped",
      "completed",
      "cancelled",
    ];
    const labels = statuses.map(orderStatusLabel);
    expect(new Set(labels).size).toBe(statuses.length);
  });

  it("formats an ISO timestamp for display", () => {
    expect(formatOrderDate("2026-10-07T09:30:00Z")).toMatch(/2026/);
  });

  it("produces unique idempotency keys", () => {
    expect(newIdempotencyKey()).not.toBe(newIdempotencyKey());
  });
});
