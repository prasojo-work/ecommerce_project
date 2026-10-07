import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { CatalogFilters } from "@/components/CatalogFilters";
import type { Category } from "@/lib/api";

const { push } = vi.hoisted(() => ({ push: vi.fn() }));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
  usePathname: () => "/products",
}));

const categories: Category[] = [
  { id: 1, name: "Living room", slug: "living-room" },
  { id: 2, name: "Bedroom", slug: "bedroom" },
];

function renderFilters(overrides: Partial<{ q: string; category: string; sort: string }> = {}) {
  return render(
    <CatalogFilters
      categories={categories}
      q={overrides.q ?? ""}
      category={overrides.category ?? ""}
      sort={overrides.sort ?? "newest"}
    />,
  );
}

describe("CatalogFilters", () => {
  beforeEach(() => {
    push.mockClear();
  });

  it("navigates with the search query on submit", () => {
    renderFilters();
    fireEvent.change(screen.getByLabelText("Search products"), { target: { value: "sofa" } });
    fireEvent.submit(screen.getByRole("search"));
    expect(push).toHaveBeenCalledWith("/products?q=sofa");
  });

  it("navigates when a category is selected", () => {
    renderFilters();
    fireEvent.change(screen.getByLabelText("Category"), { target: { value: "bedroom" } });
    expect(push).toHaveBeenCalledWith("/products?category=bedroom");
  });

  it("navigates when the sort order changes", () => {
    renderFilters();
    fireEvent.change(screen.getByLabelText("Sort by"), { target: { value: "price" } });
    expect(push).toHaveBeenCalledWith("/products?sort=price");
  });

  it("preserves other filters when one changes", () => {
    renderFilters({ q: "sofa" });
    fireEvent.change(screen.getByLabelText("Sort by"), { target: { value: "-price" } });
    expect(push).toHaveBeenCalledWith("/products?q=sofa&sort=-price");
  });
});
