import { describe, expect, it } from "vitest";

import { eventLabel, formatDate, statusClass, statusLabel } from "./orders";

describe("the order status", () => {
  it("names all five the API sends", () => {
    expect(statusLabel("pending")).toBe("Awaiting payment");
    expect(statusLabel("paid")).toBe("Paid");
    expect(statusLabel("shipped")).toBe("Shipped");
    expect(statusLabel("delivered")).toBe("Delivered");
    expect(statusLabel("cancelled")).toBe("Cancelled");
  });

  it("shows a status it has never seen as itself rather than as nothing", () => {
    // A status added to `OrderStatus` before it is added here must still be readable: a blank badge
    // would hide the order's state, and an unfamiliar word at least tells the truth.
    expect(statusLabel("refunded")).toBe("refunded");
  });
});

describe("the status badge", () => {
  it("reserves the danger colour for the one status that is bad news", () => {
    expect(statusClass("cancelled")).toContain("danger");
    expect(statusClass("paid")).not.toContain("danger");
    expect(statusClass("delivered")).not.toContain("danger");
  });
});

describe("the status timeline", () => {
  it("describes an event by the status it arrived at", () => {
    expect(eventLabel("pending")).toBe("Order placed");
    expect(eventLabel("paid")).toBe("Payment captured");
  });

  it("falls back to naming the status it moved to", () => {
    expect(eventLabel("refunded")).toBe("Moved to refunded");
  });
});

describe("a date on an order", () => {
  it("renders the day it happened, in a form a reader can scan", () => {
    // Mid-year and mid-month, so no time zone can move it into a different year or month.
    const rendered = formatDate("2026-06-15T12:00:00Z");

    expect(rendered).toContain("2026");
    expect(rendered).toContain("Jun");
  });
});
