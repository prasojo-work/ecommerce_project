import { expect, test } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import path from "node:path";

/**
 * Captures the operator console (`M5.1`, `ADR-0007`) for the README.
 *
 * The console is not part of the customer journey — it needs an `is_staff` account, and the
 * journey spec only ever creates customers — so it is a spec of its own, and it **skips** unless
 * credentials are supplied. That keeps CI honest: the pipeline has no operator, and a skipped
 * test says so rather than inventing one. `RUNBOOK.md` §9 makes the account this expects.
 *
 * The console is served by the API, not the storefront (`API.md` §9 fixes `/admin/` there), so it
 * has a base URL of its own rather than sharing the one the storefront specs audit.
 *
 *   ADMIN_EMAIL=… ADMIN_PASSWORD=… CONSOLE_BASE_URL=http://127.0.0.1:8000 \
 *     SHOTS_DIR=../docs/assets/screenshots pnpm console:audit
 */

const SHOTS_DIR = process.env.SHOTS_DIR;
const BASE_URL = process.env.CONSOLE_BASE_URL ?? "http://127.0.0.1:8000";
const EMAIL = process.env.ADMIN_EMAIL ?? "";
const PASSWORD = process.env.ADMIN_PASSWORD ?? "";

/** The console's own screens are long; the top of each is the part a README can use. */
async function shoot(page: import("@playwright/test").Page, name: string): Promise<void> {
  if (SHOTS_DIR === undefined || SHOTS_DIR === "") {
    return;
  }

  const file = path.join(SHOTS_DIR, `${name}.png`);
  await mkdir(path.dirname(file), { recursive: true });
  await page.screenshot({ path: file, fullPage: false });
}

test.describe("@console", () => {
  test.skip(
    EMAIL === "" || PASSWORD === "",
    "set ADMIN_EMAIL and ADMIN_PASSWORD to capture the operator console",
  );

  test("an operator signs in, reads the catalogue, and opens an order", async ({ page }) => {
    // 1. The console's own sign-in, which is form-and-session based rather than bearer-token.
    await page.goto(`${BASE_URL}/admin/login/?next=/admin/`);
    await page.locator('input[name="username"]').fill(EMAIL);
    await page.locator('input[name="password"]').fill(PASSWORD);
    await page.getByRole("button", { name: /log in/i }).click();
    await expect(page).toHaveURL(/\/admin\/$/);

    // 2. The catalogue, with the filters, the search box and the low-stock indicator (`US-5.3`).
    await page.goto(`${BASE_URL}/admin/catalog/product/`);
    await expect(page.getByRole("heading", { name: /select product to change/i })).toBeVisible();
    await shoot(page, "12-admin-products");

    // 3. The orders, then one order — where the receipt is read-only and the status moves only
    //    through the guarded actions the API itself calls (`US-5.4`, `US-5.5`).
    await page.goto(`${BASE_URL}/admin/orders/order/`);
    await expect(page.getByRole("heading", { name: /select order to change/i })).toBeVisible();
    await shoot(page, "13-admin-orders");

    await page.locator("table#result_list tbody th a").first().click();
    await expect(page.getByRole("heading", { name: /change order/i })).toBeVisible();
    await expect(page.getByText("History")).toBeVisible();
    await shoot(page, "14-admin-order-detail");
  });
});
