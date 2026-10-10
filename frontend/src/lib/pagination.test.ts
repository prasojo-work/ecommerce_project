import { describe, expect, it } from "vitest";

import { PAGE_SIZE, pageCount, parsePage } from "./pagination";

describe("parsePage", () => {
  it("reads a page number from the query", () => {
    expect(parsePage("3")).toBe(3);
  });

  it("starts at page one when the query is absent", () => {
    expect(parsePage(undefined)).toBe(1);
  });

  it("takes the first value when the parameter is repeated", () => {
    expect(parsePage(["2", "5"])).toBe(2);
  });

  it("falls back to page one for anything the API would answer with a 400", () => {
    for (const value of ["0", "-3", "abc", ""]) {
      expect(parsePage(value)).toBe(1);
    }
  });

  it("leaves a page past the end alone", () => {
    // Not clamped on purpose: the API returns an empty page there rather than a 404, which is how
    // the storefront renders its no-products state.
    expect(parsePage("99")).toBe(99);
  });
});

describe("pageCount", () => {
  it("counts the pages a full catalog needs", () => {
    expect(pageCount(46)).toBe(2);
  });

  it("does not add a page when the total divides evenly", () => {
    expect(pageCount(48)).toBe(2);
  });

  it("still has a first page when there is nothing to show", () => {
    expect(pageCount(0)).toBe(1);
  });

  it("matches the page size the grid requests", () => {
    expect(PAGE_SIZE).toBe(24);
    expect(pageCount(PAGE_SIZE)).toBe(1);
    expect(pageCount(PAGE_SIZE + 1)).toBe(2);
  });
});
