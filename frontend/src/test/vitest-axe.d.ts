import type { AxeMatchers } from "vitest-axe";

/**
 * Teaches Vitest's own `Assertion` about `toHaveNoViolations` (`M6.2`).
 *
 * `vitest-axe@0.1.0` ships its augmentation against the **global `Vi` namespace**:
 *
 *     declare global { namespace Vi { interface Assertion<T = any> extends AxeMatchers {} } }
 *
 * That was Jest's (and early Vitest's) surface. Vitest 5 declares `Assertion<R, T>` inside its own
 * module and no longer reads the global namespace, so the matcher runs perfectly and type-checks as
 * missing — which `next build` and `pnpm typecheck` both fail on, because they check every file in
 * the project including the tests.
 *
 * Augmenting the `vitest` module is the supported replacement, and the two parameter names are
 * spelled out rather than defaulted so the merge is against Vitest's actual arity (`R` is the
 * matcher's return, `T` the value under assertion) instead of a look-alike interface of my own.
 *
 * This file is a `.d.ts` with a top-level `import type`, which is what makes it a module and its
 * `declare module` an augmentation rather than a shadowing redefinition.
 */
declare module "vitest" {
  /* eslint-disable @typescript-eslint/no-empty-object-type, @typescript-eslint/no-unused-vars --
     Both rules read a declaration-merge contract as slack. An augmentation must declare no members
     of its own and repeat Vitest's arity exactly, and `R`/`T` go unused *because* `AxeMatchers` is
     what supplies the members this line exists to merge in. */
  interface Assertion<R = void, T = unknown> extends AxeMatchers {}
  interface AsymmetricMatchersContaining extends AxeMatchers {}
  /* eslint-enable @typescript-eslint/no-empty-object-type, @typescript-eslint/no-unused-vars */
}
