// @vitest-environment jsdom

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ProductGallery } from "@/components/product-gallery";
import { audit } from "@/test/axe";

const IMAGES = [
  { alt: "Aalto Chair in oak, seen from the front", path: "/images/aalto.webp", position: 0 },
];

describe("ProductGallery", () => {
  it("has no WCAG 2.1 AA violations", async () => {
    const { container } = render(<ProductGallery images={IMAGES} />);

    expect(await audit(container)).toHaveNoViolations();
  });

  it("describes the image with the alt text the data carries", () => {
    render(<ProductGallery images={IMAGES} />);

    expect(screen.getByAltText("Aalto Chair in oak, seen from the front")).toBeDefined();
  });

  it("renders nothing rather than a broken frame when there are no images", () => {
    const { container } = render(<ProductGallery images={[]} />);

    expect(container.innerHTML).toBe("");
  });
});
