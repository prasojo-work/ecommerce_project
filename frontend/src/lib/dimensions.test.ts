import { describe, expect, it } from "vitest";

import { dimensionParts } from "./dimensions";

describe("dimensionParts", () => {
  it("lists all three dimensions, width first", () => {
    expect(dimensionParts({ width_cm: 180, height_cm: 75, depth_cm: 90 })).toEqual([
      "Width 180 cm",
      "Depth 90 cm",
      "Height 75 cm",
    ]);
  });

  it("keeps decimals rather than rounding them", () => {
    expect(dimensionParts({ width_cm: 92.5, height_cm: 41, depth_cm: 38.25 })).toEqual([
      "Width 92.5 cm",
      "Depth 38.25 cm",
      "Height 41 cm",
    ]);
  });

  it("names only the dimensions the product declares", () => {
    // Labelling is the point: `90 × 41` would not say which measurement is missing.
    expect(dimensionParts({ width_cm: 90, height_cm: 41 })).toEqual([
      "Width 90 cm",
      "Height 41 cm",
    ]);
  });

  it("returns nothing when the product declares none", () => {
    expect(dimensionParts({})).toEqual([]);
    expect(dimensionParts({ width_cm: null, height_cm: null, depth_cm: null })).toEqual([]);
  });
});
