import { describe, expect, it } from "vitest";

import {
  addressLines,
  emptyValues,
  fieldErrors,
  headingFor,
  toCreatePayload,
  toUpdatePayload,
  validate,
  valuesFrom,
  type AddressValues,
} from "./address-form";

/**
 * The bounds checked here are `AddressCreateSchema`'s own, so a value that is too long is refused
 * with a sentence beside the input rather than by a `400` — and on SQLite the database refuses
 * nothing at all, which `M1.2` found the hard way.
 */

const complete: AddressValues = {
  label: "",
  recipient: "Ada Lovelace",
  line1: "12 Analytical Way",
  line2: "",
  city: "London",
  region: "",
  postalCode: "N1 9AB",
  country: "GB",
  phone: "",
  isDefault: false,
};

const stored = {
  id: 7,
  label: "Home",
  recipient: "Ada Lovelace",
  line1: "12 Analytical Way",
  line2: "Flat 2",
  city: "London",
  region: "",
  postal_code: "N1 9AB",
  country: "GB",
  phone: "",
  is_default: true,
};

describe("validate", () => {
  it("passes an address with only the required fields filled in", () => {
    expect(validate(complete)).toEqual({});
  });

  it("asks for each required field that is blank, and says which one", () => {
    const messages = validate({
      ...complete,
      recipient: "   ",
      line1: "",
      city: "",
      postalCode: "",
      country: "",
    });

    expect(messages.recipient).toBe("Enter who the parcel is for.");
    expect(messages.line1).toBe("Enter the street address.");
    expect(messages.city).toBe("Enter the city.");
    expect(messages.postalCode).toBe("Enter the postal code.");
    expect(messages.country).toBe("Enter the two-letter country code.");
  });

  it("does not ask for the optional fields", () => {
    // `label`, `line2`, `region` and `phone` default to "" in the API, so requiring them here would
    // refuse an address the server would have stored.
    const messages = validate(complete);

    expect(messages.label).toBeUndefined();
    expect(messages.line2).toBeUndefined();
    expect(messages.region).toBeUndefined();
    expect(messages.phone).toBeUndefined();
  });

  it("names the model's bound for a value that is too long", () => {
    const messages = validate({
      ...complete,
      recipient: "a".repeat(121),
      postalCode: "b".repeat(33),
      label: "c".repeat(61),
    });

    expect(messages.recipient).toContain("120");
    expect(messages.postalCode).toContain("32");
    expect(messages.label).toContain("60");
  });

  it("explains a country that is not a two-letter code, rather than its length", () => {
    // Three letters breaks both rules, and the second message is the one worth showing: "at most 2
    // characters" does not tell anyone what to type.
    expect(validate({ ...complete, country: "GBR" }).country).toBe(
      "Use the two-letter country code, for example GB.",
    );
    expect(validate({ ...complete, country: "G" }).country).toContain("two-letter");
  });

  it("does not measure the fields for length once they are blank", () => {
    // The optional fields are unlimited in the sense that matters: blank is always acceptable.
    expect(validate({ ...complete, label: "", line2: "", phone: "" })).toEqual({});
  });
});

describe("fieldErrors", () => {
  it("names the API's fields as this form's inputs are named", () => {
    // `postal_code` is the one that cannot be guessed from the input's name, which is why the table
    // in `address-form.ts` is the translation both ways.
    const errors = fieldErrors([
      { field: "body.postal_code", issue: "String should have at most 32 characters" },
      { field: "city", issue: "Field required" },
    ]);

    expect(errors).toEqual({
      postalCode: "String should have at most 32 characters",
      city: "Field required",
    });
  });

  it("drops an issue for a field this form does not show", () => {
    // The realistic case is `is_default`, which the API refuses with a `409` and no field at all.
    // The form still shows the envelope's own message, so nothing is hidden — it is only not pinned
    // to an input.
    expect(
      fieldErrors([{ field: "body.is_default", issue: "An address must be the default." }]),
    ).toEqual({});
  });
});

describe("payloads", () => {
  it("trims what is sent and upper-cases the country", () => {
    const payload = toCreatePayload({
      ...complete,
      recipient: "  Ada Lovelace  ",
      country: "gb",
      isDefault: true,
    });

    expect(payload.recipient).toBe("Ada Lovelace");
    expect(payload.country).toBe("GB");
    expect(payload.is_default).toBe(true);
  });

  it("never sends `is_default` on an update", () => {
    // The API refuses to let a default be cleared, so the edit form has no checkbox to untick and
    // the `PATCH` carries no opinion about the flag at all.
    const payload = toUpdatePayload({ ...complete, isDefault: true });

    expect(payload).not.toHaveProperty("is_default");
    expect(payload.city).toBe("London");
  });

  it("turns a stored address back into the values the inputs hold", () => {
    // The round trip the edit form depends on: snake_case out of the API, camelCase into the form,
    // and back to the API's names on submit.
    const values = valuesFrom(stored);

    expect(values.postalCode).toBe("N1 9AB");
    expect(values.isDefault).toBe(true);
    expect(toCreatePayload(values).postal_code).toBe("N1 9AB");
  });
});

describe("display", () => {
  it("leads with the label when there is one, and the recipient when there is not", () => {
    expect(headingFor(stored)).toBe("Home");
    expect(headingFor({ ...stored, label: "" })).toBe("Ada Lovelace");
  });

  it("repeats the recipient under a label, because 'Home' does not say who collects the parcel", () => {
    expect(addressLines(stored)[0]).toBe("Ada Lovelace");
    expect(addressLines({ ...stored, label: "" })[0]).toBe("12 Analytical Way");
  });

  it("joins the city, region and postal code into one line", () => {
    expect(addressLines({ ...stored, label: "", region: "Greater London" })).toContain(
      "London, Greater London, N1 9AB",
    );
  });

  it("omits the lines that are empty", () => {
    const lines = addressLines({ ...stored, label: "", line2: "", phone: "" });

    expect(lines).toEqual(["12 Analytical Way", "London, N1 9AB", "GB"]);
  });

  it("puts the phone last, because it is the least about the place", () => {
    expect(addressLines({ ...stored, phone: "+44 20 7946 0000" }).at(-1)).toBe("+44 20 7946 0000");
  });
});

describe("emptyValues", () => {
  it("is what the add form starts from: nothing filled in, nothing default", () => {
    expect(emptyValues()).toEqual({
      label: "",
      recipient: "",
      line1: "",
      line2: "",
      city: "",
      region: "",
      postalCode: "",
      country: "",
      phone: "",
      isDefault: false,
    });
  });
});
