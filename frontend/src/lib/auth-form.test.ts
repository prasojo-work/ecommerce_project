import { describe, expect, it } from "vitest";

import { validate } from "./auth-form";

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
