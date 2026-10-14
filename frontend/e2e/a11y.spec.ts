import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

/**
 * The route-level accessibility audit (`M6.2`, `SCOPE.md` `NFR-2`).
 *
 * This is the half that jsdom cannot do. The component tests in `src/` run axe in jsdom, which has no
 * layout engine: axe's `color-contrast` rule comes back **incomplete** there rather than passing, and
 * nothing geometric or focus-related can be trusted. A browser resolves computed styles and the real
 * accessibility tree, so contrast, target size and landmark structure are measured rather than
 * assumed. `docs/06-quality/A11Y-PERF-REPORT.md` states which of the two found what, because a green
 * run of either one alone would be a weaker claim than it looks.
 *
 * Scoped to WCAG 2.1 level A and AA, which is the level `NFR-2` names. axe's `best-practice` set is
 * left out on purpose — the same reason `src/test/axe.ts` leaves it out — so a failure here is a
 * failure against the standard the project actually promised.
 *
 * The audited set is the public routes plus the signed-out shells. The authenticated ones (a filled
 * cart, checkout, an order) need a session, and the refresh cookie is `Lax` and not `Secure`
 * locally, so an audit of those is a separate job rather than a `beforeAll` hook pretending to be one.
 */

const API = process.env.A11Y_API_URL ?? "http://127.0.0.1:8000";

const WCAG_21_AA = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"];

/**
 * The product detail route needs a real slug, and the seed owns which ones exist. Asking the API
 * rather than hard-coding one means the audit follows the seed instead of going stale the first time
 * a product is renamed — a 404 would otherwise audit Next's not-found page and pass.
 */
let productSlug = "";

test.beforeAll(async ({ request }) => {
  const response = await request.get(`${API}/api/v1/products`, { params: { page_size: 1 } });

  expect(response.ok(), `the audit needs the API seeded and reachable at ${API}`).toBeTruthy();

  const body = (await response.json()) as { items?: { slug: string }[] };
  productSlug = body.items?.[0]?.slug ?? "";

  expect(productSlug, "the seeded catalog returned no products").not.toBe("");
});

/**
 * A function per path rather than a string, because `productSlug` is only known once `beforeAll` has
 * run — by which time Playwright has already collected the tests from this list.
 */
const ROUTES: { name: string; path: () => string }[] = [
  { name: "home", path: () => "/" },
  { name: "catalog listing", path: () => "/products" },
  { name: "catalog listing, filtered and paged", path: () => "/products?q=chair&sort=-price" },
  { name: "product detail", path: () => `/products/${productSlug}` },
  { name: "credits", path: () => "/pages/credits" },
  { name: "sign in", path: () => "/login" },
  { name: "register", path: () => "/register" },
  { name: "cart, signed out", path: () => "/cart" },
  { name: "checkout, signed out", path: () => "/checkout" },
  { name: "orders, signed out", path: () => "/orders" },
  { name: "account, signed out", path: () => "/account" },
];

for (const route of ROUTES) {
  test(`${route.name} (${route.path()}) has no WCAG 2.1 AA violations`, async ({ page }) => {
    await page.goto(route.path());

    const results = await new AxeBuilder({ page }).withTags(WCAG_21_AA).analyze();

    // The message carries the rule, the impact and the selector, so a failure in the log is enough
    // to act on without re-running the audit by hand.
    const found = results.violations.map(
      (violation) =>
        `${violation.id} [${violation.impact}] -> ${violation.nodes
          .map((node) => node.target.join(" "))
          .join(", ")}`,
    );

    expect(found, `${route.path()} violates ${WCAG_21_AA.join("/")}`).toEqual([]);
  });
}
