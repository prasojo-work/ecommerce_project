import { expect as base, test, type Page } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import path from "node:path";

/**
 * The signed-in journey, end to end in a browser (`M7.3`).
 *
 * This is the one thing in the repository that no other layer can check. Every backend test shares a
 * process with the code it exercises, the `M6.2` audits never leave the anonymous half of the app,
 * and `curl` cannot sign in at all: the refresh token is an httpOnly cookie scoped to the auth
 * routes, so a session cannot be assembled by hand. What follows is the only place where the token,
 * the cart, the quote, the order, the mock payment and the history are all carried by a real browser
 * against a real deployment.
 *
 * `A11Y_BASE_URL` selects the target, exactly as it does for the other two specs, so pointing this
 * at the deployed hosts is a one-variable change — which is how `RUNBOOK.md` §7.8's last open item,
 * a sign-in through the live stack, stopped being open.
 *
 * It **writes**: an account, an address, a settled order, and one unit of stock. That is why it is
 * tagged `@journey` and kept out of `pnpm audit:routes`, and why the runbook says how to delete what
 * it leaves (`RUNBOOK.md` §7.5).
 *
 * Set `SHOTS_DIR` to also write the screenshots `README.md` embeds, so the images cannot drift from
 * the app they describe:
 *
 * ```
 * SHOTS_DIR=../docs/assets/screenshots pnpm journey:audit
 * ```
 */

/**
 * `expect` with a timeout the free tier can meet. `page.setDefaultTimeout` raises the ceiling for
 * actions and navigations but **not** for assertions, so a bare `expect` still fails after five
 * seconds — which is exactly long enough for a host that is waking up to look broken.
 */
const expect = base.configure({ timeout: 60_000 });

const SHOTS_DIR = process.env.SHOTS_DIR;
const EMAIL = process.env.JOURNEY_EMAIL ?? "browser-check@example.com";
const PASSWORD = process.env.JOURNEY_PASSWORD ?? "correct-horse-9!";
const NAME = process.env.JOURNEY_NAME ?? "Browser Check";

test.describe("@journey", () => {
  test("a shopper signs in, buys, and reads the order back", async ({ page }) => {
    // The free tier sleeps. A cold first paint measured 48 s on 2026-10-12 (`RUNBOOK.md` §7.8), so
    // the defaults are raised rather than tripping over a host that is merely waking up.
    test.setTimeout(300_000);
    page.setDefaultTimeout(60_000);
    page.setDefaultNavigationTimeout(120_000);

    await signInOrRegister(page);

    // 1. Where a sign-in lands.
    await expect(page).toHaveURL(/\/account$/);
    await shoot(page, "01-account");

    // The account is dedicated to this journey, so the cart is emptied before it is filled: a re-run
    // then produces the same screenshots rather than one line more than the last. It leaves the
    // browser on `/cart`, which is why it runs after the assertion above and not before it.
    await emptyCart(page);

    // 2. The storefront.
    await page.goto("/");
    await expect(page.getByRole("link", { name: "LYSHEIM" })).toBeVisible();
    await shoot(page, "02-home");

    // 3. The catalogue, and a product that can actually be bought. Which products are in stock is
    //    data rather than markup, so the spec asks the page instead of assuming a slug.
    await page.goto("/products");
    await shoot(page, "03-catalog");
    await openAnOrderableProduct(page);

    // 4. The product page, with a colour chosen.
    const variant = page.locator('input[name="variant"]:not([disabled])').first();
    if ((await variant.count()) > 0) {
      await variant.check();
    }
    await shoot(page, "04-product");

    await page.getByRole("button", { name: "Add to cart" }).click();
    await expect(page.getByRole("status")).toContainText("Added to your cart");

    // 5. The cart the add filled.
    await page.goto("/cart");
    await expect(page.getByRole("link", { name: "Proceed to checkout" })).toBeVisible();
    await shoot(page, "05-cart");

    // 6. Checkout, step one: where it goes. The address is entered inline because a saved one cannot
    //    exist on the first run, and this spec must work on a fresh account.
    await page.getByRole("link", { name: "Proceed to checkout" }).click();
    await expect(page).toHaveURL(/\/checkout/);
    await page.getByRole("button", { name: "Use a new address" }).click();
    await fillAddress(page);
    await shoot(page, "06-checkout-address");
    await page.getByRole("button", { name: "Deliver here" }).click();

    // 7. Shipping: a choice, then the total it produces. The quote is a round trip, so this is the
    //    assertion that needs the raised ceiling most.
    await expect(page.getByRole("heading", { name: "How should it travel?" })).toBeVisible();
    await page.locator('input[name="shipping-method"]').first().check();
    await shoot(page, "07-checkout-shipping");
    await page.getByRole("button", { name: "Continue to payment" }).click();

    // 8. Payment: the review, and the mock's two outcomes. This run takes the one that settles.
    await expect(page.getByRole("heading", { name: "Pay" })).toBeVisible();
    await shoot(page, "08-checkout-payment");
    await page.getByRole("button", { name: "Pay now" }).click();

    // 9. Confirmation, and the number the rest of the journey is addressed by.
    const confirmation = page.locator("#confirmation-heading");
    await expect(confirmation).toContainText(/LSH-[A-Z0-9]+/);
    const number = (await confirmation.textContent())?.match(/LSH-[A-Z0-9]+/)?.[0] ?? "";
    expect(number, "the confirmation named no order").not.toBe("");
    await shoot(page, "09-confirmation");

    // 10. The history, reached the way a customer reaches it.
    await page.getByRole("link", { name: "Orders" }).click();
    await expect(page).toHaveURL(/\/orders$/);
    await expect(page.getByRole("link", { name: new RegExp(number) })).toBeVisible();
    await shoot(page, "10-orders");

    // 11. The receipt and its timeline.
    await page.getByRole("link", { name: new RegExp(number) }).click();
    await expect(page).toHaveURL(new RegExp(`/orders/${number}$`));
    await expect(page.getByText(number).first()).toBeVisible();
    await shoot(page, "11-order-detail");
  });
});

/** Signs in, registering first if the account does not exist yet. */
async function signInOrRegister(page: Page): Promise<void> {
  await page.goto("/register");
  await page.getByLabel("Name").fill(NAME);
  await page.getByLabel("Email").fill(EMAIL);
  await page.getByLabel("Password").fill(PASSWORD);
  await page.getByRole("button", { name: "Create account" }).click();

  // A registration for an email that already exists is refused and the form stays put with an alert
  // on it. That is the steady state after the first run, not a failure, so the fallback is a sign-in.
  if (!(await landedOnAccount(page))) {
    await page.goto("/login");
    await page.getByLabel("Email").fill(EMAIL);
    await page.getByLabel("Password").fill(PASSWORD);
    await page.getByRole("button", { name: "Sign in" }).click();
    expect(await landedOnAccount(page), "neither registration nor sign-in reached /account").toBe(
      true,
    );
  }

  // The header is the only place the session becomes visible, and it holds a quiet row while the
  // token is restored (`M2.4`), so the account entry is what to wait for rather than a blank header.
  await expect(page.getByRole("button", { name: "Sign out" })).toBeVisible();
}

/**
 * Waits for whichever of the form's two outcomes arrives — a navigation to `/account`, or the alert
 * it renders on a refusal — and reports which. Both waits are bounded and neither is allowed to
 * reject, because the one that does not happen is not an error here.
 *
 * The refusal is scoped to the `form`, and that scoping is the whole trick: Next.js keeps a route
 * announcer in the layout as a `role="alert"` live region, so the bare role matches on *every* page
 * and settles this race before the form has answered anything.
 */
async function landedOnAccount(page: Page): Promise<boolean> {
  await Promise.race([
    page.waitForURL("**/account", { timeout: 45_000 }).catch(() => undefined),
    page
      .locator("form")
      .getByRole("alert")
      .first()
      .waitFor({ state: "visible", timeout: 45_000 })
      .catch(() => undefined),
  ]);

  return new URL(page.url()).pathname === "/account";
}

/**
 * From the open catalogue, opens products until one can be added to the cart, and leaves the browser
 * on that product. Which products are in stock is data rather than markup, so this asks the page
 * rather than assuming a slug.
 */
async function openAnOrderableProduct(page: Page): Promise<void> {
  const hrefs = await page
    .locator('a[href^="/products/"]')
    .evaluateAll((nodes) =>
      Array.from(new Set(nodes.map((node) => (node as HTMLAnchorElement).getAttribute("href")))),
    );

  expect(hrefs.length, "the catalogue linked no products").toBeGreaterThan(0);

  for (const href of hrefs.slice(0, 12)) {
    if (href === null) {
      continue;
    }

    await page.goto(href);
    const add = page.getByRole("button", { name: "Add to cart" });

    if ((await add.count()) > 0 && (await add.isEnabled())) {
      return;
    }
  }

  throw new Error("none of the first twelve products could be added to the cart");
}

/** Empties the cart through the UI, so a re-run starts from a known cart. */
async function emptyCart(page: Page): Promise<void> {
  await page.goto("/cart");

  const remove = page.getByRole("button", { name: "Remove", exact: true });

  // Bounded rather than `while (true)`: a loop with a network call inside it is one refused request
  // away from hanging the suite rather than failing it.
  for (let remaining = await remove.count(); remaining > 0; remaining = await remove.count()) {
    if (remaining > 10) {
      throw new Error(
        `the cart held ${String(remaining)} lines, which is not this journey's doing`,
      );
    }

    await remove.first().click();
    await expect(remove).toHaveCount(remaining - 1);
  }
}

/** Fills the address book's own form, which checkout reuses. */
async function fillAddress(page: Page): Promise<void> {
  await page.getByLabel("Recipient").fill(NAME);
  await page.getByLabel("Phone").fill("+1 555 0100");
  await page.getByLabel("Address", { exact: true }).fill("14 Blackthorn Row");
  await page.getByLabel("Address line 2").fill("Floor 3");
  await page.getByLabel("City").fill("Portland");
  await page.getByLabel("Region").fill("OR");
  await page.getByLabel("Postal code").fill("97205");
  await page.getByLabel("Country").fill("US");
}

/**
 * Writes one screenshot, when `SHOTS_DIR` is set.
 *
 * Full-page, because a README wants the whole screen rather than the top of it — and after a scroll
 * pass, because `next/image` loads below-the-fold images lazily and a full-page capture taken
 * without one holds empty boxes where the photographs are.
 */
async function shoot(page: Page, name: string): Promise<void> {
  if (SHOTS_DIR === undefined || SHOTS_DIR === "") {
    return;
  }

  await page.evaluate(async () => {
    await new Promise<void>((resolve) => {
      let y = 0;
      const step = (): void => {
        y += window.innerHeight;
        window.scrollTo(0, y);
        if (y < document.body.scrollHeight) {
          setTimeout(step, 120);
        } else {
          window.scrollTo(0, 0);
          setTimeout(resolve, 300);
        }
      };
      step();
    });
  });

  const file = path.join(SHOTS_DIR, `${name}.png`);
  await mkdir(path.dirname(file), { recursive: true });
  await page.screenshot({ path: file, fullPage: true });
}
