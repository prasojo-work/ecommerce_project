import { describe, expect, it } from "vitest";

import { FEATURED_COUNT, selectFeatured } from "./featured";
import type { ProductCard } from "@/api/client";

function card(slug: string, category: string, amountCents: number): ProductCard {
  return {
    id: amountCents,
    slug,
    name: slug,
    material: "Oak",
    color: "Natural",
    in_stock: true,
    category: { slug: category, name: category },
    price: { amount_cents: amountCents, currency: "USD" },
    image: null,
  };
}

describe("selectFeatured", () => {
  it("takes one piece per category, in the order given", () => {
    // Input is price-descending, so "first of each category" is also the priciest of each.
    const pool = [
      card("chest", "bedroom", 218500),
      card("side-table", "living-room", 188100),
      card("bench", "living-room", 186900),
      card("wardrobe", "bedroom", 185200),
      card("lamp", "lighting", 24000),
    ];

    expect(selectFeatured(pool).map((product) => product.slug)).toEqual([
      "chest",
      "side-table",
      "lamp",
    ]);
  });

  it("skips a cheaper member of a category it has already used", () => {
    const pool = [
      card("sofa", "living-room", 90000),
      card("armchair", "living-room", 80000),
      card("rug", "textiles", 40000),
    ];

    expect(selectFeatured(pool, 2).map((product) => product.slug)).toEqual(["sofa", "rug"]);
  });

  it("stops at the count, not at the number of categories", () => {
    const pool = ["a", "b", "c", "d", "e", "f"].map((slug, index) =>
      card(slug, `cat-${index}`, 10000 - index),
    );

    expect(selectFeatured(pool)).toHaveLength(FEATURED_COUNT);
  });

  it("returns what it has when the pool is narrower than the count", () => {
    // A catalogue with two categories cannot fill a four-piece row, and should not pretend to.
    const pool = [card("a", "one", 100), card("b", "two", 90), card("c", "one", 80)];

    expect(selectFeatured(pool).map((product) => product.slug)).toEqual(["a", "b"]);
  });

  it("returns nothing for an empty pool", () => {
    expect(selectFeatured([])).toEqual([]);
  });

  it("does not mutate its argument", () => {
    const pool = [card("a", "one", 100), card("b", "two", 90)];
    const before = [...pool];

    selectFeatured(pool);

    expect(pool).toEqual(before);
  });
});
