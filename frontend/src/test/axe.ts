import { configureAxe } from "vitest-axe";

/**
 * The axe runner the component tests use.
 *
 * `SCOPE.md` `NFR-2` asks for **WCAG 2.1 AA**, so the runner is scoped to exactly that: the A and AA
 * rule sets of 2.1 and nothing else. axe also ships a `best-practice` set, which is worth reading and
 * is not what the project promised — a red test has to mean "this breaks WCAG 2.1 AA", or the
 * difference between a defect and a preference gets argued in the test output rather than in review.
 *
 * `configureAxe` rather than a per-call options object so the scope is declared once and every test
 * that renders markup is measured against the same rules.
 */
export const audit = configureAxe({
  runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"] },
});
