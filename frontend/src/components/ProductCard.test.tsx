import type { ReactNode } from "react";

import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ProductCard } from "@/components/ProductCard";
import type { ProductListItem } from "@/lib/api";

vi.mock("next/link", () => ({
  default: ({ href, children }: { href: string; children: ReactNode }) => (
    <a href={href}>{children}</a>
  ),
}));

const product: ProductListItem = {
  id: 1,
  title: "Nordvik Sofa",
  slug: "nordvik-sofa",
  category: { id: 1, name: "Living room", slug: "living-room" },
  brand: "Nordvik",
  price_from: 4_200_000,
  currency: "IDR",
  image: null,
};

describe("ProductCard", () => {
  it("renders the category, title and starting price", () => {
    render(<ProductCard product={product} />);
    expect(screen.getByText("Living room")).toBeInTheDocument();
    expect(screen.getByText("Nordvik Sofa")).toBeInTheDocument();
    expect(screen.getByText(/4\.200\.000/)).toBeInTheDocument();
  });

  it("links to the product detail page", () => {
    render(<ProductCard product={product} />);
    expect(screen.getByRole("link")).toHaveAttribute("href", "/products/nordvik-sofa");
  });
});
