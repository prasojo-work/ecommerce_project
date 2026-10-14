// @vitest-environment jsdom

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { EmptyState } from "@/components/empty-state";
import { audit } from "@/test/axe";

describe("EmptyState", () => {
  it("has no WCAG 2.1 AA violations in either variant", async () => {
    const filtered = render(
      <EmptyState
        title="No products match those filters"
        description="Try a different price band, or clear the search."
        action={<button type="button">Clear filters</button>}
      />,
    );

    expect(await audit(filtered.container)).toHaveNoViolations();

    const bare = render(<EmptyState title="No products yet" />);

    expect(await audit(bare.container)).toHaveNoViolations();
  });

  it("reports the empty state as a heading, not as a paragraph of text", () => {
    // The screen's own `<h1>` is the page title, so this is deliberately level 2: a reader moving by
    // heading should land on the page first and on the absence second.
    render(<EmptyState title="No products yet" />);

    expect(screen.getByRole("heading", { level: 2, name: "No products yet" })).toBeDefined();
  });

  it("leaves out the description and the action when the caller has neither", () => {
    render(<EmptyState title="No products yet" />);

    expect(screen.queryByRole("button")).toBeNull();
    expect(screen.queryByText(/try a different/i)).toBeNull();
  });
});
