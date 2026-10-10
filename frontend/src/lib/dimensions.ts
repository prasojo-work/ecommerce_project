type Dimensions = {
  width_cm?: number | null;
  height_cm?: number | null;
  depth_cm?: number | null;
};

/**
 * Labelled dimensions, skipping any the product does not declare.
 *
 * The API's three dimensions are independently nullable, so they are labelled and listed rather
 * than joined into a bare `180 × 90 × 75`: a product carrying two of the three would otherwise be
 * ambiguous about which one is missing. `UX-GOAL-1` asks for dimensions before the cart, so they
 * are surfaced on the detail page rather than left to the cart.
 */
export function dimensionParts(dimensions: Dimensions): string[] {
  const labelled: [string, number | null | undefined][] = [
    ["Width", dimensions.width_cm],
    ["Depth", dimensions.depth_cm],
    ["Height", dimensions.height_cm],
  ];

  return labelled
    .filter((entry): entry is [string, number] => typeof entry[1] === "number")
    .map(([label, value]) => `${label} ${value} cm`);
}
