import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ProductGallery } from "@/components/ProductGallery";
import type { ProductImage } from "@/lib/api";

vi.mock("next/image", () => ({
  default: ({ src, alt }: { src: string; alt: string }) => <img src={src} alt={alt} />,
}));

const images: ProductImage[] = [
  { url: "https://img.example/one.jpg", alt: "One" },
  { url: "https://img.example/two.jpg", alt: "Two" },
];

describe("ProductGallery", () => {
  it("shows the first image plus one thumbnail per image", () => {
    render(<ProductGallery images={images} title="Nordvik Sofa" />);
    expect(screen.getAllByRole("img")).toHaveLength(3);
    expect(screen.getAllByRole("img")[0]).toHaveAttribute("src", images[0].url);
    expect(screen.getAllByRole("button")).toHaveLength(2);
  });

  it("switches the main image when a thumbnail is selected", () => {
    render(<ProductGallery images={images} title="Nordvik Sofa" />);
    expect(screen.getAllByRole("img")[0]).toHaveAttribute("src", images[0].url);
    fireEvent.click(screen.getAllByRole("button")[1]);
    expect(screen.getAllByRole("img")[0]).toHaveAttribute("src", images[1].url);
  });

  it("renders a placeholder when there are no images", () => {
    render(<ProductGallery images={[]} title="Nordvik Sofa" />);
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
  });
});
