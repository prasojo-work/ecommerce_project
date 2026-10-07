import type { ReactNode } from "react";

import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ProductDetailView } from "@/components/ProductDetailView";
import type { ProductDetail } from "@/lib/api";

vi.mock("next/link", () => ({
  default: ({ href, children }: { href: string; children: ReactNode }) => (
    <a href={href}>{children}</a>
  ),
}));

vi.mock("next/image", () => ({
  default: ({ src, alt }: { src: string; alt: string }) => <img src={src} alt={alt} />,
}));

const product: ProductDetail = {
  id: 1,
  title: "Nordvik Sofa",
  slug: "nordvik-sofa",
  description: "A compact sofa.",
  brand: "Nordvik",
  category: { id: 1, name: "Living room", slug: "living-room" },
  base_price: 5_000_000,
  currency: "IDR",
  images: [{ url: "https://img.example/sofa.jpg", alt: "Sofa" }],
  variants: [
    {
      id: 1,
      sku: "SOFA-A",
      name: "Fog grey",
      attributes: { colour: "Fog grey" },
      price: 5_000_000,
      stock_qty: 3,
      is_active: true,
    },
    {
      id: 2,
      sku: "SOFA-B",
      name: "Deep green",
      attributes: { colour: "Deep green" },
      price: 4_200_000,
      stock_qty: 0,
      is_active: true,
    },
  ],
};

describe("ProductDetailView", () => {
  it("shows the brand, title, breadcrumb and description", () => {
    render(<ProductDetailView product={product} />);
    expect(screen.getByRole("heading", { level: 1, name: "Nordvik Sofa" })).toBeInTheDocument();
    expect(screen.getByText("Nordvik")).toBeInTheDocument();
    expect(screen.getByText("Living room")).toBeInTheDocument();
    expect(screen.getByText("A compact sofa.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Shop" })).toHaveAttribute("href", "/products");
  });

  it("uses the cheapest active variant as the headline price", () => {
    render(<ProductDetailView product={product} />);
    const prices = screen.getAllByText(/Rp\s?4\.200\.000/);
    expect(prices.length).toBeGreaterThan(0);
  });

  it("lists every variant with its stock status", () => {
    render(<ProductDetailView product={product} />);
    expect(screen.getByText("Fog grey")).toBeInTheDocument();
    expect(screen.getByText("Deep green")).toBeInTheDocument();
    expect(screen.getByText("In stock")).toBeInTheDocument();
    expect(screen.getByText("Out of stock")).toBeInTheDocument();
  });

  it("renders a disabled add-to-cart button", () => {
    render(<ProductDetailView product={product} />);
    expect(screen.getByRole("button", { name: /add to cart/i })).toBeDisabled();
  });
});
