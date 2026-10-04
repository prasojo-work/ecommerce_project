# ADR-0003: JWT authentication (access + refresh)

- **Status:** Accepted
- **Date:** 2026-10-04
- **Deciders:** Founder
- **Related:** `ADR-0002`

## Context

The Next.js client is decoupled from the Django API. We need an authentication mechanism that works cleanly across two origins/deployments, protects write endpoints, and is a realistic, defensible choice for a decoupled SPA.

## Options considered

1. **Server-side sessions (cookies)** — Django's default, robust, easy to revoke. But cross-origin cookie handling with a separate frontend needs careful `SameSite`/`Secure`/CORS configuration, and it couples the API to browser sessions.
2. **JWT access + refresh** — stateless, natural for a decoupled client, industry-conventional for SPAs/APIs. Thematic cost is token-revocation complexity.
3. **Third-party identity provider (Auth0/Supabase Auth)** — less code, but adds a dependency and reduces the *portfolio* demonstration of implementing auth.

## Decision

Use **JWT with a short-lived access token and a longer-lived refresh token**, with refresh rotation and blacklist-on-logout. This is the conventional answer for a decoupled architecture and makes the auth flow explicit and reviewable.

## Consequences

- **Positive:** clean separation of concerns; stateless API; standard, well-understood pattern; demonstrates security reasoning.
- **Negative / costs:** token storage on the client must be decided carefully (prefer `httpOnly` cookies to reduce XSS exposure); revocation requires a blacklist; short access-token lifetime adds a refresh round-trip.
- **Follow-ups:** implement silent refresh with a single retry on `401`; document the storage choice; add rate limiting on the token endpoint.

## Reversibility

**Medium.** Moving to cookie sessions or an identity provider is a contained change to the auth module and the client's request layer.
