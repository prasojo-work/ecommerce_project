import { describe, expect, it } from "vitest";

import { buildCatalogQuery, DEFAULT_SORT } from "@/lib/url";

describe("buildCatalogQuery", () => {
  it("returns an empty string when there are no filters", () => {
    expect(buildCatalogQuery({})).toBe("");
  });

  it("includes every provided filter", () => {
    expect(
      buildCatalogQuery({ q: "sofa", category: "living-room", sort: "price", page: 2 }),
    ).toBe("?q=sofa&category=living-room&sort=price&page=2");
  });

  it("omits the default sort and the first page", () => {
    expect(buildCatalogQuery({ sort: DEFAULT_SORT, page: 1 })).toBe("");
  });

  it("applies overrides on top of the current values", () => {
    expect(buildCatalogQuery({ q: "sofa", page: 2 }, { page: 3 })).toBe("?q=sofa&page=3");
  });

  it("drops a filter when the override is undefined", () => {
    expect(buildCatalogQuery({ q: "sofa", category: "bedroom" }, { category: undefined })).toBe(
      "?q=sofa",
    );
  });
});
