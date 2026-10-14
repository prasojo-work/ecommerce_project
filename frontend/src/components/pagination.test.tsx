// @vitest-environment jsdom

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Pagination } from "@/components/pagination";
import { DEFAULT_SORT, type CatalogQuery } from "@/lib/catalog-query";
import { audit } from "@/test/axe";

const FILTERED: CatalogQuery = {
  page: 2,
  sort: DEFAULT_SORT,
  q: "chair",
  category: "seating",
};

describe("Pagination", () => {
  it("has no WCAG 2.1 AA violations", async () => {
    const { container } = render(<Pagination page={2} totalPages={5} query={FILTERED} />);

    expect(await audit(container)).toHaveNoViolations();
  });

  it("is a labelled navigation landmark rather than a pair of loose links", () => {
    render(<Pagination page={2} totalPages={5} query={FILTERED} />);

    expect(screen.getByRole("navigation", { name: "Pagination" })).toBeDefined();
  });

  it("carries the current filters onto every page it links to", () => {
    // `US-1.4`: page three of a filtered view has to still be filtered when it is shared, so a
    // paging link that dropped the query would be a link to a different listing.
    render(<Pagination page={2} totalPages={5} query={FILTERED} />);

    const href = screen.getByRole("link", { name: "Next" }).getAttribute("href") ?? "";

    expect(href).toContain("page=3");
    expect(href).toContain("q=chair");
    expect(href).toContain("category=seating");
  });

  it("turns a dead end into a span rather than a link that goes nowhere", () => {
    // `US-1.4` and `NFR-2`: the end of the range is announced, not left to the muted colour.
    render(<Pagination page={1} totalPages={5} query={{ ...FILTERED, page: 1 }} />);

    expect(screen.queryByRole("link", { name: "Previous" })).toBeNull();
    expect(screen.getByText("Previous").getAttribute("aria-disabled")).toBe("true");
  });

  it("renders nothing at all when there is only one page", () => {
    const { container } = render(<Pagination page={1} totalPages={1} query={FILTERED} />);

    expect(container.innerHTML).toBe("");
  });
});
