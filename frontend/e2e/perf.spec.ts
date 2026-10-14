import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";

/**
 * The performance half of `M6.2` (`SCOPE.md` `NFR-1`).
 *
 * `NFR-1` asks for three things, and this file answers all three: an LCP under 2.5 s on a **mobile**
 * profile for the catalog and the PDP, a catalog read at p95 under 300 ms, and — the clause v1 had
 * left until now — a *documented* JS bundle budget. The budget is a constant below and the reasoning
 * for its value is in `docs/06-quality/A11Y-PERF-REPORT.md`, next to the measurement it was set from.
 *
 * Why the throttle is hand-rolled rather than taken from a Lighthouse run: the number has to be
 * reproducible by anyone with this repository and nothing else. `Emulation.setCPUThrottlingRate` and
 * `Network.emulateNetworkConditions` are the same two primitives Lighthouse drives, applied to the
 * same profile (`SCOPE.md` says p75 **mobile**), so the measurement is honest about the conditions it
 * claims and carries no second toolchain to install.
 *
 * The value of a localhost LCP is limited, and the report says so rather than dressing it up: with
 * the API on loopback and no TLS hop, this measures how much work the app does before it paints, not
 * what a shopper on a train will see. It is a regression gate, not a field measurement — p75 in the
 * field comes from the deployed URL and real traffic, which is `M7`'s job.
 *
 * Like `a11y.spec.ts`, this is no part of `pnpm test` and no part of CI: it needs a browser and a
 * whole stack behind it (the seeded API, a running build of this app), and `frontend.yml` has
 * neither.
 */

declare global {
  interface Window {
    /** The most recent `largest-contentful-paint` entry, installed before any page script runs. */
    __lcp?: number;
  }
}

const API = process.env.PERF_API_URL ?? "http://127.0.0.1:8000";

/** `NFR-1`'s own numbers, plus the bundle budget it asks to be documented. */
const BUDGET = {
  lcpMs: 2_500,
  apiP95Ms: 300,
  /**
   * 200 KiB against a first measurement of 148 KiB: about a third of headroom, so a new dependency
   * has room to land without a debate, while a regression that *doubled* the bundle still trips it.
   * A budget an order of magnitude clear of the real number is the opposite of a gate. Raising this
   * is a decision, and `docs/06-quality/A11Y-PERF-REPORT.md` is where it gets argued.
   */
  firstLoadJsBytes: 200 * 1024,
};

/** Lighthouse's mobile preset: 4× CPU, and a Slow-4G pipe at 150 ms RTT. */
const CPU_THROTTLE = 4;
const SLOW_4G = {
  latency: 150,
  downloadBytesPerSecond: (1.6 * 1024 * 1024) / 8,
  uploadBytesPerSecond: (750 * 1024) / 8,
};

let productSlug = "";

test.beforeAll(async ({ request }) => {
  // The seed owns which slugs exist, so the audit asks rather than hard-codes one — a renamed
  // product would otherwise turn this into a measurement of Next's not-found page, which is fast.
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
  { name: "catalog listing", path: () => "/products" },
  { name: "product detail", path: () => `/products/${productSlug}` },
];

test.use({ viewport: { width: 390, height: 844 } });

/**
 * The LCP observer has to exist before the first paint, so it is installed as an init script rather
 * than evaluated afterwards — a `page.evaluate` would arrive long after the entry it wants.
 */
async function observeLcp(page: Page): Promise<void> {
  await page.addInitScript(() => {
    new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        window.__lcp = entry.startTime;
      }
    }).observe({ type: "largest-contentful-paint", buffered: true });
  });
}

/**
 * Waits for the LCP to stop moving rather than for `load`.
 *
 * On a partial-prerendered route the shell paints first and the streamed half arrives later, so the
 * LCP candidate can still be replaced after `load` has fired. Reading the last value once the number
 * has held still for a beat measures the page that finished, not the first one that appeared.
 */
async function settledLcp(page: Page): Promise<number> {
  let previous = -1;
  let current = -1;

  for (let attempt = 0; attempt < 40; attempt += 1) {
    previous = current;
    current = await page.evaluate(() => window.__lcp ?? 0);

    if (current > 0 && current === previous) {
      return current;
    }

    await page.waitForTimeout(200);
  }

  return current;
}

async function throttle(page: Page): Promise<void> {
  const cdp = await page.context().newCDPSession(page);

  await cdp.send("Network.enable");
  await cdp.send("Emulation.setCPUThrottlingRate", { rate: CPU_THROTTLE });
  await cdp.send("Network.emulateNetworkConditions", {
    offline: false,
    latency: SLOW_4G.latency,
    downloadThroughput: SLOW_4G.downloadBytesPerSecond,
    uploadThroughput: SLOW_4G.uploadBytesPerSecond,
  });
}

for (const route of ROUTES) {
  test(`${route.name} (${route.path()}) paints its LCP within the mobile budget`, async ({
    page,
  }) => {
    await observeLcp(page);
    await throttle(page);
    await page.goto(route.path());

    const lcp = await settledLcp(page);

    console.log(`${route.path()} LCP ${Math.round(lcp)} ms (throttled: 4x CPU, Slow 4G)`);

    // A zero would mean the observer never fired, which is a broken measurement rather than a fast
    // page — `toBeLessThanOrEqual` alone would call it a pass.
    expect(lcp, "no largest-contentful-paint entry was recorded").toBeGreaterThan(0);
    expect(lcp, `${route.path()} LCP on a throttled mobile profile`).toBeLessThanOrEqual(
      BUDGET.lcpMs,
    );
  });

  test(`${route.name} (${route.path()}) stays within the first-load JS budget`, async ({
    page,
  }) => {
    // Unthrottled on purpose: this counts bytes, and throttling changes how long they take to
    // arrive, not how many there are.
    await page.goto(route.path());
    await page.waitForLoadState("load");

    const bytes = await page.evaluate(() =>
      performance
        .getEntriesByType("resource")
        // `lib.dom` types the return as bare `PerformanceEntry[]`, which has neither of the two
        // fields this needs — the guard is the narrowing, not a cast papering over one.
        .filter((entry): entry is PerformanceResourceTiming => entry.entryType === "resource")
        .filter((entry) => entry.initiatorType === "script" || entry.name.endsWith(".js"))
        .reduce((total, entry) => total + entry.transferSize, 0),
    );

    console.log(`${route.path()} first-load JS ${(bytes / 1024).toFixed(1)} KiB`);

    expect(bytes, "no scripts were recorded, so nothing was measured").toBeGreaterThan(0);
    expect(bytes, `${route.path()} first-load JS`).toBeLessThanOrEqual(BUDGET.firstLoadJsBytes);
  });
}

test(`catalog reads answer within the p95 budget`, async ({ request }) => {
  const SAMPLES = 24;
  const timings: number[] = [];

  for (let sample = 0; sample < SAMPLES; sample += 1) {
    const started = performance.now();
    const response = await request.get(`${API}/api/v1/products`, { params: { page_size: 12 } });

    expect(response.ok()).toBeTruthy();
    timings.push(performance.now() - started);
  }

  timings.sort((left, right) => left - right);

  // The nearest-rank definition of p95: no interpolation, because with 24 samples an interpolated
  // percentile would be inventing a request that was never made.
  const p95 = timings[Math.ceil(SAMPLES * 0.95) - 1];

  console.log(`catalog reads p95 ${p95.toFixed(1)} ms over ${SAMPLES} requests`);

  expect(p95, "catalog reads at p95").toBeLessThanOrEqual(BUDGET.apiP95Ms);
});

test("static assets ship immutable and images ship optimised", async ({ request }) => {
  const html = await (await request.get("/products")).text();

  const chunk = html.match(/\/_next\/static\/chunks\/[^"]+\.js/)?.[0] ?? "";
  expect(chunk, "the listing served no JS chunks").not.toBe("");

  const chunkResponse = await request.get(chunk);
  const chunkCache = chunkResponse.headers()["cache-control"] ?? "";

  expect(chunkResponse.status()).toBe(200);
  expect(chunkCache, "hashed chunks should never be revalidated").toContain("immutable");
  expect(chunkCache, "a year is the point of a content-hashed URL").toMatch(/max-age=\d{6,}/);

  // Every shipped image is a `next/image`, so the browser gets a `srcset` and the optimizer's own
  // cache. A plain `<img src>` here would show up as this match finding nothing.
  const image = html.match(/\/_next\/image\?url=[^"&]+&amp;w=640&amp;q=\d+/)?.[0] ?? "";
  expect(image, "the listing served no optimised images").not.toBe("");

  const imageResponse = await request.get(image.replaceAll("&amp;", "&"), {
    // What a browser sends: the optimizer negotiates on this header, and asserting the format
    // without offering any is how a JPEG gets mistaken for the worst case.
    headers: { accept: "image/avif,image/webp,image/apng,*/*" },
  });
  const imageCache = imageResponse.headers()["cache-control"] ?? "";
  const maxAge = Number(/max-age=(\d+)/.exec(imageCache)?.[1] ?? 0);

  console.log(
    `optimised image: ${imageResponse.headers()["content-type"]}, ${imageCache} ` +
      `(${imageResponse.headers()["content-length"] ?? "?"} bytes)`,
  );

  expect(imageResponse.status()).toBe(200);
  expect(imageResponse.headers()["content-type"]).toMatch(/^image\/(avif|webp|jpeg|png)/);
  expect(maxAge, "the optimizer's cache should outlive a page view").toBeGreaterThanOrEqual(3_600);
});
