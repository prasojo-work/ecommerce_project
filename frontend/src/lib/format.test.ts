import { describe, expect, it } from "vitest";

import { formatIdr } from "@/lib/format";

describe("formatIdr", () => {
  it("formats a whole-rupiah amount with the Rp prefix and dot separators", () => {
    expect(formatIdr(4_500_000)).toMatch(/Rp\s?4\.500\.000/);
  });

  it("formats zero without decimals", () => {
    expect(formatIdr(0)).toMatch(/Rp\s?0$/);
  });
});
