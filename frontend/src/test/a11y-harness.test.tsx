// @vitest-environment jsdom

import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { audit } from "@/test/axe";

/**
 * The negative control for the a11y harness itself.
 *
 * Every other test in this suite asserts that markup is *clean*, which is also what a runner that
 * silently found nothing would report. So this file points the runner at markup that is definitely
 * broken and fails if the violation does not come back. Without it, a misconfigured `runOnly`, a
 * detached container, or an axe version that stopped loading would turn the whole suite green.
 */
function Clean() {
  return (
    <main>
      <h1>Shape</h1>
      <p>A paragraph.</p>
    </main>
  );
}

function Broken() {
  return (
    <main>
      {/* A button with no text and no label: WCAG 2.1 A, "name, role, value" (`button-name`). */}
      <button type="button" />
    </main>
  );
}

describe("the a11y harness", () => {
  it("passes markup with no violations", async () => {
    const { container } = render(<Clean />);

    expect(await audit(container)).toHaveNoViolations();
  });

  it("reports a violation it is pointed at", async () => {
    const { container } = render(<Broken />);

    const results = await audit(container);

    expect(results.violations.map((violation) => violation.id)).toContain("button-name");
  });
});
