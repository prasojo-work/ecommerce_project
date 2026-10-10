import { describe, expect, it } from "vitest";

import { flattenCategories, type CategoryNode } from "./categories";

function node(slug: string, children: CategoryNode[] = []): CategoryNode {
  return { id: 1, slug, name: slug, description: "", parent_slug: null, children };
}

describe("flattenCategories", () => {
  it("returns a root on its own", () => {
    expect(flattenCategories([node("decor")])).toEqual([
      { slug: "decor", name: "decor", depth: 0 },
    ]);
  });

  it("puts a child directly after its parent, one level deeper", () => {
    // A select has no nesting, so the order has to carry the structure.
    expect(
      flattenCategories([node("living-room", [node("sofas"), node("tables")]), node("decor")]),
    ).toEqual([
      { slug: "living-room", name: "living-room", depth: 0 },
      { slug: "sofas", name: "sofas", depth: 1 },
      { slug: "tables", name: "tables", depth: 1 },
      { slug: "decor", name: "decor", depth: 0 },
    ]);
  });

  it("handles grandchildren", () => {
    expect(flattenCategories([node("a", [node("b", [node("c")])])])).toEqual([
      { slug: "a", name: "a", depth: 0 },
      { slug: "b", name: "b", depth: 1 },
      { slug: "c", name: "c", depth: 2 },
    ]);
  });

  it("returns nothing for an empty tree", () => {
    expect(flattenCategories([])).toEqual([]);
  });
});
