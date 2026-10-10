import { describe, expect, it } from "vitest";

import { licenceUrl } from "./licences";

describe("licenceUrl", () => {
  it("maps every licence the catalog ships", () => {
    // The shipped set, measured from the credit table: 33 BY, 11 BY-SA, 1 PDM, 1 CC0. If a fourth
    // code ever ships, this test is where it should be noticed.
    expect(licenceUrl("BY-2.0")).toBe("https://creativecommons.org/licenses/by/2.0/");
    expect(licenceUrl("BY-SA-2.0")).toBe("https://creativecommons.org/licenses/by-sa/2.0/");
    expect(licenceUrl("CC0-1.0")).toBe("https://creativecommons.org/publicdomain/zero/1.0/");
    expect(licenceUrl("PDM-1.0")).toBe("https://creativecommons.org/publicdomain/mark/1.0/");
  });

  it("returns null for a code it does not know, rather than guessing a deed", () => {
    // A guessed URL would claim terms the image does not carry, which is worse than plain text.
    expect(licenceUrl("BY-ND-2.0")).toBeNull();
    expect(licenceUrl("BY-4.0")).toBeNull();
    expect(licenceUrl("")).toBeNull();
  });
});
