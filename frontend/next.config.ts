import type { NextConfig } from "next";

/**
 * Response hardening for the storefront (`M6.3`, `SEC-FIND-1.4`, `SECURITY-BASELINE.md` section 6).
 *
 * The API's own `Content-Security-Policy` is set by `core.middleware` in the backend, and it is
 * inert there: those responses are JSON. This is the copy that matters, because this is the app that
 * renders HTML for a shopper, and a policy is only ever as useful as the document it arrives on.
 *
 * Three deliberate choices, each of which would look like an oversight otherwise:
 *
 * * `script-src` carries `'unsafe-inline'`. Next.js streams an inline bootstrap script into every
 *   document, and without plumbing a nonce through the App Router — a per-request nonce the
 *   `headers()` config cannot produce, since it is evaluated per build rather than per request — the
 *   choice is that concession or a site that does not hydrate. It still leaves the directive meaning
 *   something: no third-party origin can serve a script to this app, which is the injection route
 *   that matters most. Moving to nonces is the next step, and `SECURITY-REVIEW.md` records it as the
 *   residual rather than as done.
 * * `connect-src` names the API origin explicitly, because the browser calls it cross-origin for the
 *   cart, the session and orders. Without it those calls are blocked and the storefront is read-only.
 * * `upgrade-insecure-requests` is *not* set. Vercel serves this app over HTTPS and the API sets
 *   `Strict-Transport-Security`, so it would add nothing in production while rewriting the API origin
 *   during local audits — that is, it would break the `pnpm audit:routes` run that verifies these
 *   headers are still there.
 */

const isProduction = process.env.NODE_ENV === "production";

/** The same variable and the same fallback as `src/lib/config.ts`, which is what the browser calls. */
const apiOrigin = process.env.NEXT_PUBLIC_API_BASE_URL?.trim() || "http://localhost:8000";

const contentSecurityPolicy = [
  "default-src 'self'",
  "base-uri 'self'",
  "object-src 'none'",
  "frame-ancestors 'none'",
  "form-action 'self'",
  "img-src 'self' data: blob:",
  "font-src 'self'",
  "style-src 'self' 'unsafe-inline'",
  isProduction
    ? "script-src 'self' 'unsafe-inline'"
    : "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
  `connect-src 'self' ${apiOrigin}`,
].join("; ");

const nextConfig: NextConfig = {
  cacheComponents: true,
  partialPrefetching: true,
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "Content-Security-Policy", value: contentSecurityPolicy },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          {
            key: "Permissions-Policy",
            value: "camera=(), microphone=(), geolocation=(), payment=()",
          },
        ],
      },
    ];
  },
};

export default nextConfig;
