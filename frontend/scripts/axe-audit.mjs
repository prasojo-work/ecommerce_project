/**
 * Full axe-core audit over the key routes.
 *
 * Lighthouse's accessibility category runs a *subset* of axe's rules; this runs
 * the whole WCAG 2.1 A/AA set plus axe's own best-practice rules, which is what
 * "axe clean" means in the M6 exit criteria.
 *
 * Needs a production build being served:
 *
 *   pnpm build && pnpm start        # terminal 1
 *   node scripts/axe-audit.mjs      # terminal 2
 *
 * Exits non-zero when a violation is found, so it can gate CI later. Chrome comes
 * from CHROME_PATH, or from a Playwright-managed Chromium when one is installed.
 */
import { existsSync, readdirSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

import axe from "axe-core";
import puppeteer from "puppeteer-core";

const BASE_URL = process.env.BASE_URL ?? "http://localhost:3000";

// The seeded demo catalogue supplies the product slug.
const ROUTES = [
  ["home", "/"],
  ["products", "/products"],
  ["detail", "/products/sol-table-lamp"],
  ["cart", "/cart"],
  ["checkout", "/checkout"],
  ["orders", "/orders"],
  ["account", "/account"],
  ["login", "/login"],
  ["register", "/register"],
];

const TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "best-practice"];

function findChromium() {
  if (process.env.CHROME_PATH) {
    return process.env.CHROME_PATH;
  }
  const root = join(homedir(), ".cache", "ms-playwright");
  if (!existsSync(root)) {
    return undefined;
  }
  for (const entry of readdirSync(root)) {
    const candidate = join(root, entry, "chrome-linux64", "chrome");
    if (existsSync(candidate)) {
      return candidate;
    }
  }
  return undefined;
}

const browser = await puppeteer.launch({
  executablePath: findChromium(),
  args: ["--no-sandbox", "--disable-dev-shm-usage"],
});

let total = 0;

for (const [name, path] of ROUTES) {
  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 900 });
  await page.goto(`${BASE_URL}${path}`, { waitUntil: "networkidle2" });

  await page.evaluate(axe.source);
  const results = await page.evaluate(
    async (tags) => window.axe.run(document, { runOnly: { type: "tag", values: tags } }),
    TAGS,
  );

  const { violations } = results;
  total += violations.length;
  console.log(`\n${name} (${path}) — ${violations.length} violation(s)`);

  for (const violation of violations) {
    console.log(`  [${violation.impact}] ${violation.id}: ${violation.help}`);
    for (const node of violation.nodes.slice(0, 3)) {
      console.log(`      ${node.target.join(" ")}`);
      const detail = node.failureSummary?.split("\n").pop()?.trim();
      if (detail) {
        console.log(`        ${detail}`);
      }
    }
    if (violation.nodes.length > 3) {
      console.log(`      …and ${violation.nodes.length - 3} more instance(s)`);
    }
  }

  await page.close();
}

await browser.close();

console.log(`\n${total} violation(s) across ${ROUTES.length} route(s)`);
process.exit(total === 0 ? 0 : 1);
