// @vitest-environment jsdom

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { ProductCard as ProductCardData } from "@/api/client";
import { ProductCard } from "@/components/product-card";
import { audit } from "@/test/axe";

const PRODUCT: ProductCardData = {
  category: { name: "Seating", slug: "seating" },
  color: "Natural",
  id: 1,
  image: { alt: "Aalto Chair in oak, three-quarter view", path: "/images/aalto.webp", position: 0 },
  in_stock: true,
  material: "Oak",
  name: "Aalto Chair",
  price: { amount_cents: 129900, currency: "USD" },
  slug: "aalto-chair",
};

const UNDESCRIBED: ProductCardData = {
  ...PRODUCT,
  image: { alt: "", path: "/images/aalto.webp", position: 0 },
};

describe("ProductCard", () => {
  it("has no WCAG 2.1 AA violations", async () => {
    const { container } = render(<ProductCard product={PRODUCT} />);

    expect(await audit(container)).toHaveNoViolations();
  });

  it("has no violations when the image carries no description", async () => {
    // `UX.md` section 7 treats an empty `alt` as decorative, which is a legitimate answer rather
    // than a missing one — so the clean case is asserted separately from the described one.
    const { container } = render(<ProductCard product={UNDESCRIBED} />);

    expect(await audit(container)).toHaveNoViolations();
  });

  it("is a single tab stop, pointing at the product it names", () => {
    render(<ProductCard product={PRODUCT} />);

    const links = screen.getAllByRole("link");

    expect(links).toHaveLength(1);
    expect(links[0]?.getAttribute("href")).toBe("/products/aalto-chair");
    expect(screen.getByRole("heading", { name: "Aalto Chair" })).toBeDefined();
  });

  it("describes the image from the data rather than from the product name", () => {
    // The name is already a heading beside it; repeating it as the alt text would be the redundant
    // description `UX.md` section 7 asks to avoid.
    render(<ProductCard product={PRODUCT} />);

    expect(screen.getByAltText("Aalto Chair in oak, three-quarter view")).toBeDefined();
  });

  it("shows the price in the format `UX.md` section 9 fixes", () => {
    render(<ProductCard product={PRODUCT} />);

    expect(screen.getByText("$1,299.00")).toBeDefined();
  });

  it("carries the spec line `UX-DIRECTION.md` section 4 rule 2 requires", () => {
    // Rule 2: "No product tile without a spec line." Material, finish and availability were all in
    // the payload and all discarded before `M7.4`, which is why the tile read as a price tag.
    render(<ProductCard product={PRODUCT} />);

    expect(screen.getByText("Oak · Natural · In stock")).toBeDefined();
  });

  it("says out of stock in words, not only in colour", () => {
    render(<ProductCard product={{ ...PRODUCT, in_stock: false }} />);

    expect(screen.getByText("Oak · Natural · Out of stock")).toBeDefined();
  });

  it("drops the parts a product does not declare rather than printing empty separators", () => {
    // `material` and `color` are both `blank=True`, so the line is assembled from what exists.
    // "· · In stock" would be the failure this asserts against.
    render(<ProductCard product={{ ...PRODUCT, material: "", color: "" }} />);

    expect(screen.getByText("In stock")).toBeDefined();
    expect(screen.queryByText(/·/)).toBeNull();
  });
});
