// @vitest-environment jsdom

import { render, screen } from "@testing-library/react";
import { useState } from "react";
import { describe, expect, it } from "vitest";

import { TextField } from "@/components/text-field";
import { audit } from "@/test/axe";

/**
 * `TextField` is controlled, so every case needs a stateful host. This is the smallest one.
 *
 * `UX.md` section 7 and `SCOPE.md` `NFR-2` make the wiring the point: the sentence beside the input
 * has to belong to the input for a screen reader, and it has to be text rather than a colour.
 */
function Harness({ error }: { error?: string }) {
  const [value, setValue] = useState("");
  return (
    <TextField
      id="email"
      label="Email"
      value={value}
      error={error}
      onChange={setValue}
      autoComplete="email"
    />
  );
}

describe("TextField", () => {
  it("has no WCAG 2.1 AA violations, with and without an error", async () => {
    const clean = render(<Harness />);

    expect(await audit(clean.container)).toHaveNoViolations();

    const failing = render(<Harness error="That email is already registered." />);

    expect(await audit(failing.container)).toHaveNoViolations();
  });

  it("points the input at the error it is failing on", () => {
    render(<Harness error="That email is already registered." />);

    const input = screen.getByLabelText("Email");

    expect(input.getAttribute("aria-invalid")).toBe("true");
    expect(input.getAttribute("aria-describedby")).toBe("email-error");
    expect(screen.getByText("That email is already registered.").id).toBe("email-error");
  });

  it("claims no error state when there is none", () => {
    render(<Harness />);

    const input = screen.getByLabelText("Email");

    // `aria-invalid` is spelled out as "false" rather than omitted: the attribute is set from a
    // boolean, and an assistive technology reading the explicit value is what the component promises.
    expect(input.getAttribute("aria-invalid")).toBe("false");
    expect(input.hasAttribute("aria-describedby")).toBe(false);
  });

  it("does not rely on the browser's own validation bubble", () => {
    render(<Harness />);

    // `required` and `maxLength` are deliberately absent: the browser's bubble would be a second
    // voice on the page saying something different from every other message on it.
    const input = screen.getByLabelText("Email");

    expect(input.hasAttribute("required")).toBe(false);
    expect(input.hasAttribute("maxlength")).toBe(false);
  });
});
