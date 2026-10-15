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

## Rotation, reuse detection, and the interrupted reply

Not part of the original decision, but the contract the implementation settled into, recorded here
because the code points at this ADR for it.

- Every refresh **rotates**: the presented token is revoked, a successor is issued, and the row
  records which token superseded it (`RefreshToken.replaced_by`).
- Presenting an already-revoked token is **reuse**, and reuse revokes every live token the account
  has. The decisive signal is that a token was revoked *and its successor was spent*: the legitimate
  client received the successor, so a second holder of the old one means a copy.
- A successor that was **never spent** is the one case that is not reuse. A browser that navigates
  away while its refresh is in flight is handed the cancellation rather than the new cookie, so the
  replacement went nowhere and nobody has ever held it — and the next page load presents the old
  token again. Read strictly, that revoked every session the customer had, on every device, for a
  reply that never arrived.
- So while the replacement is unspent and no older than `REFRESH_ROTATION_GRACE_SECONDS` (120 s by
  default), the replay is treated as that retry: the replacement is withdrawn, the presented token
  is pointed at a fresh successor, and a pair is issued.

**The bound, stated plainly:** inside that grace a stolen-but-superseded token is exchangeable
rather than detected. The window is what keeps the trade small — past it, and once a successor has
been spent, reuse ends the session exactly as it did before.

## References

- `docs/02-product/SCOPE.md` §8 (D3)
- `docs/03-architecture/API.md` §2
