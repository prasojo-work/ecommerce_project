import type { components } from "@/api/schema";

export type CategoryNode = components["schemas"]["CategorySchema"];

export type FlatCategory = { slug: string; name: string; depth: number };

/**
 * Flatten the category tree into the order a `<select>` needs.
 *
 * The API nests categories (`CategoryTreeSchema`) and a `category` filter matches descendants, so
 * the storefront has to render a tree as one list of options. Depth is returned rather than baked
 * into the label, leaving the indent a rendering decision.
 */
export function flattenCategories(nodes: CategoryNode[], depth = 0): FlatCategory[] {
  return nodes.flatMap((node) => [
    { slug: node.slug, name: node.name, depth },
    ...flattenCategories(node.children ?? [], depth + 1),
  ]);
}
