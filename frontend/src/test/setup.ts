import { cleanup } from "@testing-library/react";
import { afterEach, expect } from "vitest";
import * as matchers from "vitest-axe/matchers";

// `vitest-axe` extends `expect` with `toHaveNoViolations` and re-exports axe-core's runner. The
// matchers are registered once per process, which is what a setup file is for — doing it per test
// file would work and would also mean every new a11y test has to remember to.
//
// `vitest-axe/extend-expect` is a side-effect import that adds the matcher to Vitest's `expect`
// *types*; without it `toHaveNoViolations` type-checks as missing even though it runs.
import "vitest-axe/extend-expect";

expect.extend(matchers);

// React Testing Library unmounts after each test only when it can find a global `afterEach`, which
// Vitest does not provide by default. Wiring it here rather than in each test file keeps the DOM from
// accumulating across cases in one file, which is what makes `screen.getByRole` start matching twice.
afterEach(cleanup);
