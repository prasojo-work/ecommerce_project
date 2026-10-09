# ADR-0009 — Authentication and token storage (D3)

- **Status:** Accepted
- **Date:** 2026-10-09
- **Deciders:** Founder
- **Consulted hats:** senior_backend, senior_cybersecurity, senior_frontend_engineering

## Context

The frontend is a decoupled SPA-style app talking to a separate API, so cookie-only session
auth is awkward, while naive token storage has known XSS exposure. **Decision D3** was left
open: where do tokens live? The answer must be secure by default and compatible with a
cross-origin deployment (Vercel frontend, Render API).

## Options considered

1. **localStorage (access + refresh).** Pros: simplest. Cons: any XSS can exfiltrate
   long-lived credentials; widely considered poor practice.
2. **httpOnly refresh cookie + short-lived access token in memory.** Pros: refresh token is
   unreadable by JavaScript, so XSS cannot steal long-term access; access token is short-lived
   and never persisted. Cons: needs a refresh flow and correct cross-site cookie attributes.
3. **Session cookie only (drop JWTs).** Pros: simplest cookies. Cons: couples the API to
   browser clients and weakens the "decoupled API" story.

## Decision

Use **option 2**:

- A short-lived **access token** (JWT, ~15 min) returned in the response body and held **in
  memory** by the client — never in `localStorage`/`sessionStorage`.
- A **refresh token** in an **httpOnly, Secure, SameSite=None cookie** (required for the
  cross-site Vercel↔Render setup; `Lax` locally), scoped to the refresh endpoint path.
- A silent refresh on 401; logout invalidates the refresh token server-side and clears the
  cookie.
- The refresh endpoint enforces an origin check plus the refresh cookie to defend against
  CSRF, since cookie auth reintroduces that risk.

## Consequences

- XSS can no longer steal a long-lived credential; the blast radius of a token leak is one
  short-lived access token.
- Requires correct CORS (**credentials**), cookie attributes, and a CSRF guard on refresh —
  all documented and tested.
- Slightly more client code (refresh interceptor) than localStorage.

## Reversibility

**Moderate.** The token *issuing* is independent of storage; changing transport later is
contained to the auth module and the client interceptor.

## References

- `docs/02-product/SCOPE.md` §8 (D3)
- `docs/03-architecture/API.md` §2
