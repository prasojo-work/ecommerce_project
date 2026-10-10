import { describe, expect, it } from "vitest";

import {
  DEFAULT_SORT,
  PRICE_BANDS,
  bandParams,
  isBandActive,
  isFiltered,
  parseCatalogQuery,
  toQueryParams,
  type CatalogQuery,
} from "./catalog-query";

describe("parseCatalogQuery", () => {
  it("defaults to the first page, the API's sort, and no filters", () => {
    expect(parseCatalogQuery({})).toEqual({ page: 1, sort: DEFAULT_SORT });
  });

  it("reads every filter the contract defines", () => {
    expect(
      parseCatalogQuery({
        q: "  chair  ",
        category: "decor",
        min_price: "10000",
        max_price: "25000",
        sort: "-price",
        page: "3",
      }),
    ).toEqual({
      page: 3,
      sort: "-price",
      q: "chair",
      category: "decor",
      minPrice: 10000,
      maxPrice: 25000,
    });
  });

  it("falls back for anything the API would answer with a 400", () => {
    expect(parseCatalogQuery({ sort: "cheapest" }).sort).toBe(DEFAULT_SORT);
    expect(parseCatalogQuery({ sort: "" }).sort).toBe(DEFAULT_SORT);
    expect(parseCatalogQuery({ min_price: "-5" }).minPrice).toBeUndefined();
    expect(parseCatalogQuery({ max_price: "12.5" }).maxPrice).toBeUndefined();
    expect(parseCatalogQuery({ max_price: "abc" }).maxPrice).toBeUndefined();
    expect(parseCatalogQuery({ page: "0" }).page).toBe(1);
  });

  it("treats blank fields as absent, because a submitted form sends empty strings", () => {
    expect(parseCatalogQuery({ q: "", category: "", min_price: "", max_price: "" })).toEqual({
      page: 1,
      sort: DEFAULT_SORT,
    });
  });

  it("accepts a zero bound, which is valid rather than missing", () => {
    expect(parseCatalogQuery({ min_price: "0" }).minPrice).toBe(0);
  });

  it("keeps an unknown category so the API can answer with no results", () => {
    // The API returns zero results for an unknown category filter rather than a 404; validating it
    // away here would turn US-1.3's no-results state into a silently unfiltered listing.
    expect(parseCatalogQuery({ category: "not-a-category" }).category).toBe("not-a-category");
  });

  it("takes the first value when a parameter repeats", () => {
    expect(parseCatalogQuery({ q: ["chair", "lamp"] }).q).toBe("chair");
    expect(parseCatalogQuery({ page: ["2", "9"] }).page).toBe(2);
  });
});

describe("isFiltered", () => {
  const base: CatalogQuery = { page: 1, sort: DEFAULT_SORT };

  it("is false when only paging or sorting is set", () => {
    expect(isFiltered(base)).toBe(false);
    expect(isFiltered({ ...base, page: 4, sort: "-price" })).toBe(false);
  });

  it("is true for each narrowing filter", () => {
    expect(isFiltered({ ...base, q: "chair" })).toBe(true);
    expect(isFiltered({ ...base, category: "decor" })).toBe(true);
    expect(isFiltered({ ...base, minPrice: 0 })).toBe(true);
    expect(isFiltered({ ...base, maxPrice: 25000 })).toBe(true);
  });
});

describe("toQueryParams", () => {
  const base: CatalogQuery = { page: 1, sort: DEFAULT_SORT };

  it("omits what sits at its default, so shared links stay short", () => {
    expect(toQueryParams(base)).toEqual({});
    expect(toQueryParams({ ...base, page: 1, sort: DEFAULT_SORT })).toEqual({});
  });

  it("uses the API's parameter names", () => {
    expect(
      toQueryParams({ page: 2, sort: "-price", q: "chair", category: "decor", minPrice: 10000 }),
    ).toEqual({
      q: "chair",
      category: "decor",
      min_price: "10000",
      sort: "-price",
      page: "2",
    });
  });

  it("round-trips through parseCatalogQuery, which is what makes a link shareable", () => {
    const query: CatalogQuery = {
      page: 3,
      sort: "price",
      q: "oak",
      category: "storage",
      minPrice: 10000,
      maxPrice: 25000,
    };

    expect(parseCatalogQuery(toQueryParams(query))).toEqual(query);
  });

  it("can target another page while keeping the filters", () => {
    const query: CatalogQuery = { page: 1, sort: DEFAULT_SORT, q: "oak" };

    expect(toQueryParams(query, 2)).toEqual({ q: "oak", page: "2" });
  });
});

describe("price bands", () => {
  const base: CatalogQuery = { page: 1, sort: DEFAULT_SORT };

  it("expresses a band as contract parameters", () => {
    expect(bandParams(PRICE_BANDS[0])).toEqual({ max_price: "10000" });
    expect(bandParams(PRICE_BANDS[1])).toEqual({ min_price: "10000", max_price: "25000" });
    expect(bandParams(PRICE_BANDS[3])).toEqual({ min_price: "75000" });
    expect(bandParams(null)).toEqual({});
  });

  it("knows which band is applied, and that none applied means any price", () => {
    expect(isBandActive(base, null)).toBe(true);
    expect(isBandActive(base, PRICE_BANDS[0])).toBe(false);

    const first = parseCatalogQuery(bandParams(PRICE_BANDS[0]));
    expect(isBandActive(first, PRICE_BANDS[0])).toBe(true);
    expect(isBandActive(first, null)).toBe(false);
  });

  it("leaves a hand-typed price range matching no band, rather than mislabelling it", () => {
    const custom = parseCatalogQuery({ min_price: "5000", max_price: "9000" });

    expect(PRICE_BANDS.some((band) => isBandActive(custom, band))).toBe(false);
    expect(isBandActive(custom, null)).toBe(false);
  });
});
