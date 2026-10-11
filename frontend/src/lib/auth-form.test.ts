import { describe, expect, it } from "vitest";

import { fieldMessages, fieldOf, messageForFailure, validate } from "./auth-form";

describe("fieldOf", () => {
  it("strips the parameter source Ninja prefixes a pydantic error with", () => {
    expect(fieldOf("body.email")).toBe("email");
    expect(fieldOf("query.q")).toBe("q");
    expect(fieldOf("path.slug")).toBe("slug");
  });

  it("leaves an error the endpoint raised itself alone", () => {
    // This is the shape `API.md` section 3 documents for a duplicate address, and it is not the
    // same shape as a pydantic failure — a mapper that only understands one drops the other.
    expect(fieldOf("email")).toBe("email");
  });

  it("keeps the nesting after the source, so a nested field stays addressable", () => {
    expect(fieldOf("body.address.line1")).toBe("address.line1");
  });

  it("does not treat a field that merely starts with the same letters as a prefix", () => {
    expect(fieldOf("bodyguard")).toBe("bodyguard");
  });
});

describe("fieldMessages", () => {
  it("maps every reported field, whichever shape it arrived in", () => {
    const messages = fieldMessages([
      { field: "body.password", issue: "This password is too short." },
      { field: "email", issue: "duplicate" },
    ]);

    expect(messages).toEqual({
      password: "This password is too short.",
      email: "duplicate",
    });
  });

  it("keeps the first issue when a field is reported twice", () => {
    const messages = fieldMessages([
      { field: "body.password", issue: "first" },
      { field: "body.password", issue: "second" },
    ]);

    expect(messages.password).toBe("first");
  });

  it("ignores an entry with no field", () => {
    expect(fieldMessages([{ field: "", issue: "somewhere" }])).toEqual({});
  });
});

describe("validate", () => {
  const filled = { email: "ada@example.com", password: "correct-horse-9!", displayName: "" };

  it("passes a complete sign-in", () => {
    expect(validate("login", filled)).toEqual({});
  });

  it("passes a complete registration without a display name", () => {
    // `RegisterSchema.display_name` defaults to "", so requiring it here would refuse a
    // registration the API accepts.
    expect(validate("register", { ...filled, displayName: "" })).toEqual({});
  });

  it("asks for an email address", () => {
    expect(validate("login", { ...filled, email: "  " }).email).toBe("Enter your email address.");
  });

  it("questions an email address that is not one", () => {
    expect(validate("login", { ...filled, email: "ada@example" }).email).toContain("not look like");
  });

  it("asks for a password", () => {
    expect(validate("login", { ...filled, password: "" }).password).toBe("Enter your password.");
  });

  it("requires eight characters to register", () => {
    expect(validate("register", { ...filled, password: "short" }).password).toContain("8");
  });

  it("accepts exactly eight characters", () => {
    expect(validate("register", { ...filled, password: "8charsok" }).password).toBeUndefined();
  });

  it("does not judge the length of a sign-in password", () => {
    // The server does not either, and a customer whose password predates a policy change must still
    // be able to sign in.
    expect(validate("login", { ...filled, password: "old" })).toEqual({});
  });
});

describe("messageForFailure", () => {
  it("uses the API's own message when there is one", () => {
    expect(messageForFailure(401, "Incorrect email or password.")).toBe(
      "Incorrect email or password.",
    );
  });

  it("says what to do about a rate limit, not just that there is one", () => {
    // `UX.md` flow D names the rate-limited state; `Too many requests.` states the fact and leaves
    // the customer with nothing to act on.
    expect(messageForFailure(429, "Too many requests.")).toContain("wait a moment");
  });
});
