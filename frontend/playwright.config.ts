import { defineConfig, devices } from "@playwright/test";

/**
 * The config behind the two `M6.2` audits: `pnpm axe:audit` (`NFR-2`, `e2e/a11y.spec.ts`) and
 * `pnpm perf:audit` (`NFR-1`, `e2e/perf.spec.ts`). `pnpm audit:routes` runs both.
 *
 * `audit:routes` rather than `audit`, because `pnpm audit` is pnpm's *own* dependency check and this
 * repository already depends on it meaning that — `SECURITY-BASELINE.md` and the `M6.3` checklist
 * both call it for the lockfile audit. A script shadowing the built-in would quietly turn a security
 * command into an accessibility one at the prompt, and nothing would look wrong.
 *
 * Deliberately **not** part of `pnpm test` and deliberately not wired into CI. A route-level audit
 * needs a browser and a whole stack behind it — the Django API with seed data, and a running build of
 * this app. `frontend.yml` has neither: it builds partial-prerendered shells with nothing serving
 * `NEXT_PUBLIC_API_BASE_URL`, and adding Postgres and Python to the frontend job would be a large
 * amount of CI to prove something about markup that the component tests already guard.
 *
 * What it proves is the half jsdom cannot, and the report says so plainly: jsdom has no layout, so
 * axe's `color-contrast` rule comes back *incomplete* rather than passing, and anything geometric or
 * focus-related is guesswork there. Here it is measured.
 *
 * `A11Y_BASE_URL` is the target, so the same spec can audit a deployed environment without an edit.
 */
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  forbidOnly: true,
  retries: 0,
  workers: 1,
  reporter: [["list"]],
  use: {
    baseURL: process.env.A11Y_BASE_URL ?? "http://127.0.0.1:3000",
    trace: "off",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
