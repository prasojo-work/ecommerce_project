import { unstable_rethrow } from "next/navigation";
import createClient from "openapi-fetch";

import { getApiBaseUrl } from "@/lib/config";

import type { components, paths } from "./schema";

export type ProductCard = components["schemas"]["ProductCardSchema"];
export type ProductPage = components["schemas"]["ProductPageSchema"];
export type ProductDetail = components["schemas"]["ProductDetailSchema"];

/**
 * The catalog read client.
 *
 * `paths` comes from `src/api/schema.d.ts`, which `pnpm codegen` rebuilds from the backend's
 * committed snapshot. The route, the query names, and the response shape therefore cannot drift
 * from `M1.3` without this file failing the type check — which is the whole point of `M1.4`.
 */
const client = createClient<paths>({
  baseUrl: getApiBaseUrl(),
  // Resolved on every call rather than captured once when this module loads. Next replaces the
  // global `fetch` to add request memoisation, and a reference captured at import time can predate
  // that replacement — which would quietly turn one product read into two.
  fetch: (request) => fetch(request),
});

export type ProductsResult = { ok: true; data: ProductPage } | { ok: false; message: string };

/**
 * One page of the catalog.
 *
 * Failures are returned rather than thrown, so the page can render a retry panel next to its
 * heading instead of losing the whole route to an error boundary.
 *
 * The request is deliberately uncached. `Cache Components` would let it join the static shell
 * behind `use cache`, but nothing invalidates the catalog yet, so a reseed would keep serving
 * withdrawn products until the cache lifetime expired. Correctness first: caching wants an
 * invalidation story to go with it.
 */
export async function fetchProducts(page: number, pageSize: number): Promise<ProductsResult> {
  try {
    const { data, response } = await client.GET("/api/v1/products", {
      params: { query: { page, page_size: pageSize } },
    });

    if (data) {
      return { ok: true, data };
    }

    // The schema documents only `200` responses, so openapi-fetch cannot type the body of a
    // failure. The status is the reliable signal, and it belongs in the server log rather than
    // in copy a customer reads (`UX.md` section 9 forbids jargon).
    console.error(`catalog: GET /api/v1/products answered ${response.status} for page ${page}`);
    return { ok: false, message: "The catalog service is having trouble right now." };
  } catch (error) {
    // Partial Prerendering aborts a request-time `fetch` once the shell's prerender finishes, and
    // Next signals that by throwing. That rejection is not a failure and must not be reported as
    // one: `unstable_rethrow` passes framework errors through so React can complete the abort, and
    // the docs name `fetch` with `cache: 'no-store'` as a case that has to be rethrown rather than
    // caught. Without it every build logs a backend outage that never happened.
    unstable_rethrow(error);
    console.error("catalog: GET /api/v1/products did not complete", error);
    return { ok: false, message: "The catalog service could not be reached." };
  }
}

export type ProductDetailResult =
  | { ok: true; product: ProductDetail }
  | { ok: false; kind: "not-found" }
  | { ok: false; kind: "unavailable"; message: string };

/**
 * One product, with its gallery and variants (`US-1.2`).
 *
 * A missing product is separated from an unavailable service because the two want different
 * treatment: the API answers an unknown slug with a `404` (`catalog/api.py`), which the page turns
 * into Next's `notFound()` and a real `404` status, while a failure gets the retry panel.
 */
export async function fetchProduct(slug: string): Promise<ProductDetailResult> {
  try {
    const { data, response } = await client.GET("/api/v1/products/{slug}", {
      params: { path: { slug } },
    });

    if (data) {
      return { ok: true, product: data };
    }

    if (response.status === 404) {
      return { ok: false, kind: "not-found" };
    }

    console.error(`catalog: GET /api/v1/products/{slug} answered ${response.status} for ${slug}`);
    return {
      ok: false,
      kind: "unavailable",
      message: "The catalog service is having trouble right now.",
    };
  } catch (error) {
    // Rethrown for the same reason as above: Partial Prerendering aborts a request-time fetch with
    // an internal error that must reach React rather than be reported as an outage.
    unstable_rethrow(error);
    console.error(`catalog: GET /api/v1/products/{slug} did not complete for ${slug}`, error);
    return {
      ok: false,
      kind: "unavailable",
      message: "The catalog service could not be reached.",
    };
  }
}
