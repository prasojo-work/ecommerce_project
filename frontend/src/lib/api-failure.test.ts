import { describe, expect, it } from "vitest";

import { asFailure, fieldMessages, fieldOf, messageForFailure } from "./api-failure";

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

describe("asFailure", () => {
  const response = new Response(null, { status: 400 });

  it("reads the envelope the API sends", () => {
    const failure = asFailure(
      {
        error: {
          code: "VALIDATION_ERROR",
          message: "Some fields need attention.",
          details: [{ field: "body.city", issue: "Field required" }],
        },
      },
      response,
    );

    expect(failure).toEqual({
      ok: false,
      code: "VALIDATION_ERROR",
      message: "Some fields need attention.",
      details: [{ field: "body.city", issue: "Field required" }],
      status: 400,
    });
  });

  it("survives a responder that is not the API", () => {
    // A proxy or a cold start answering HTML is the case this exists for: the form must be able to
    // say something rather than throw while reading `undefined.error`.
    const failure = asFailure("<html>502 Bad Gateway</html>", new Response(null, { status: 502 }));

    expect(failure.code).toBe("ERROR");
    expect(failure.message).toContain("try again");
    expect(failure.details).toEqual([]);
    expect(failure.status).toBe(502);
  });

  it("survives a response with no body at all", () => {
    const failure = asFailure(undefined, new Response(null, { status: 503 }));

    expect(failure.status).toBe(503);
    expect(failure.details).toEqual([]);
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
