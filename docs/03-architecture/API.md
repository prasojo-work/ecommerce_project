# API Contract — LYSHEIM

> Consulted hat: **Senior Backend** with **Senior Frontend**. Owner: Founder.
> Base URL: `/api/v1`. Framework: **Django Ninja**, which emits an **OpenAPI 3** schema the
> frontend consumes (see `ADR-0005`). This document is the human-readable contract; the
> generated `/api/v1/openapi.json` is the machine one.

---

## 1. Conventions

- **Format:** JSON in, JSON out; UTF-8; `Content-Type: application/json`.
- **Versioning:** path-based (`/api/v1/`). Breaking changes create `/api/v2/`.
- **Naming:** `snake_case` for JSON fields; plural resource nouns.
- **Timestamps:** ISO-8601 UTC (`2026-10-09T12:00:00Z`).
- **Money:** integer minor units plus a `currency` (`{"amount_cents": 18000, "currency": "USD"}`).
- **Auth:** `Authorization: Bearer <access_token>` on protected routes.
- **Cross-origin:** the web app runs on its own origin, so `CORS_ALLOWED_ORIGINS` decides who may
  read a response and credentials are allowed so the refresh cookie travels. That same list is what
  the origin guard on `/auth/refresh` compares against — one list, so the two cannot drift apart.

## 2. Authentication

Refresh tokens are delivered as an **httpOnly, Secure, SameSite cookie**; the access token is
returned in the response body and held **in memory** by the client (`ADR-0009`).

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/auth/register` | none | Create account; returns tokens |
| POST | `/auth/login` | none | Authenticate; returns access token + sets refresh cookie |
| POST | `/auth/refresh` | cookie | New access token from the refresh cookie |
| POST | `/auth/logout` | access | Invalidate refresh; clear cookie |
| GET | `/auth/me` | access | Current user profile |
| PATCH | `/auth/me` | access | Update the profile (`display_name`) |

Auth endpoints are **rate-limited**; a `429` carries `Retry-After` in whole seconds and the
`RATE_LIMITED` code. Limits are **per client, not per account**: keying on a submitted address would
let anyone lock a known account out of its own sign-in screen, which turns a rate limit into a
denial-of-service tool. The numbers are configuration rather than contract
(`NINJA_DEFAULT_THROTTLE_RATES`), and the limit applies to the endpoint rather than to failures — a
client that has exhausted it is refused a correct password too, until the window passes.

`POST /auth/refresh` additionally checks the request's **origin** against `CORS_ALLOWED_ORIGINS` and
answers `403` `FORBIDDEN` when it does not match. The refresh token is a credential the browser
attaches by itself, and in production the cookie is `SameSite=None` for the Vercel-to-Render call, so
this check is what stands in for that attribute (`ADR-0009`). The check runs before the cookie is
read, so a forged request cannot spend a token — or revoke one. A request carrying neither `Origin`
nor `Referer` is allowed through: that is a non-browser client, and no page can prevent a browser from
sending one.

`register` and `login` answer with `{access_token, token_type, expires_in, user}`. The refresh token
is deliberately **not** in the body: it is set as an httpOnly cookie scoped to `/api/v1/auth`, so
only `POST /auth/refresh` is ever sent it (`ADR-0009`). `refresh` rotates that cookie, and answers
`401` when the token is missing, expired, unreadable or already revoked. `logout` answers `204` and
ends the session server-side; `me` returns the current account.

`PATCH /auth/me` accepts `{display_name}` and returns the updated account. A field left out of the
body is left **unchanged**, so an empty object is a no-op rather than a clear — the difference
between editing a name and erasing one (`US-2.4`).

## 3. Error envelope

Every error response uses one shape (see `NFR-4`):

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed.",
    "details": [{"field": "body.email", "issue": "That email is already registered."}],
    "request_id": "01J9Z3K8Q2M4"
  }
}
```

Each `details` entry is `{field, issue}`, and `field` is the location with its source still on it —
`body.email` for a rejected request body, `query.q` for a query parameter — so a client can tell a
bad query string from a bad body. The view parameter's own name is **not** part of the field: the API
reports `body.country`, never `body.payload.country`. Clients match an input by stripping the source
prefix, and must cope with it being absent, because an error raised before a body is parsed has no
source to name.

Status codes: `400` validation, `401` unauthenticated, `403` forbidden, `404` not found,
`409` conflict (e.g. stock), `422` semantic error, `429` rate-limited, `500` unexpected.
`request_id` is echoed in the `X-Request-ID` response header.

## 4. Catalog (public)

| Method | Path | Query / Notes |
|---|---|---|
| GET | `/categories` | Tree of categories |
| GET | `/categories/{slug}` | One category + its products (paginated) |
| GET | `/products` | `category`, `q`, `min_price`, `max_price`, `sort` (`price`,`-price`,`newest`,`name`), `page`, `page_size` |
| GET | `/products/{slug}` | PDP payload: product, variants, images, availability |
| GET | `/credits` | Attribution for every shipped image (`US-6.1`); the complete list, not paginated |

Listing responses are paginated: `{ "items": [...], "page": 1, "page_size": 24, "total": 137 }`.
`/credits` is the exception: `US-6.1` wants every shipped image and there are 46, so the response is
the whole list.

## 5. Cart (authenticated)

The cart belongs to the authenticated user: every endpoint below requires an access token. An
anonymous visitor can browse the catalog but cannot hold a cart — `ADR-0017` reversed the guest
cookie and the login merge that `ADR-0008` first chose.

| Method | Path | Purpose |
|---|---|---|
| GET | `/cart` | Current cart with line items and totals, or an empty one; never creates a cart |
| POST | `/cart/items` | Add `{variant_id, quantity}` |
| PATCH | `/cart/items/{id}` | Set `{quantity}`; refused above stock |
| DELETE | `/cart/items/{id}` | Remove a line |

`409` is returned when a requested quantity exceeds available stock, `404` when the line is not in
the caller's cart, and `400` when `quantity` is below one.

## 6. Checkout & orders

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/checkout/quote` | optional | Totals + shipping options for a cart + address |
| POST | `/orders` | optional | Create order; requires `Idempotency-Key` header |
| GET | `/orders` | access | List the user's orders |
| GET | `/orders/{number}` | access | Order detail + status timeline |

Order creation is **idempotent** on the `Idempotency-Key` header (`NFR-4`), so a double submit
cannot produce two orders.

## 7. Payments (mock)

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/payments/mock/confirm` | access | Simulate capture for an order's payment |
| POST | `/payments/mock/fail` | access | Simulate a declined payment (for QA of the failure path) |

These endpoints exist **only** while `PAYMENT_PROVIDER=mock` (`ADR-0010`). They are removed
when a real provider is integrated.

## 8. Addresses (authenticated)

Requires `Authorization: Bearer <access_token>`; `401` without one. Every route is scoped to the
caller, and an address belonging to another account is a **`404`, never a `403`** — `403` would
confirm that the id exists, which is what an attempt to enumerate addresses wants to learn.

| Method | Path | Purpose |
|---|---|---|
| GET | `/addresses` | List the caller's addresses, default first |
| POST | `/addresses` | Create; `201` with the stored address |
| PATCH | `/addresses/{address_id}` | Update the fields present in the body |
| DELETE | `/addresses/{address_id}` | Remove; `204` with no body |

An address is `{id, label, recipient, line1, line2, city, region, postal_code, country, phone,
is_default}`. Only `recipient`, `line1`, `city`, `postal_code` and `country` are required; the rest
default to empty, and `country` is a two-letter ISO-3166 code.

**Exactly one default.** For as long as an account has any address, one of them is the default: the
first address created becomes it whether or not the client asked, promoting another demotes the
previous one, and deleting the default promotes the oldest survivor. Clearing the default outright is
refused with `409` `CONFLICT` (`QA-C31`) — set another address as the default instead. The database
enforces *at most one* (a partial unique index per user); these routes hold the stronger rule so that
checkout never has to ask which of several defaults won.

## 9. Operations

| Method | Path | Purpose |
|---|---|---|
| GET | `/healthz` | Liveness/readiness for uptime checks (no auth, no DB models) |

The operator console is **Django admin** (`/admin/`), not part of this REST API (`ADR-0007`).

## 10. OpenAPI

- The schema is generated at `/api/v1/openapi.json` and a browsable UI at `/api/v1/docs`.
- The frontend's API client types are generated from this schema, so the contract cannot
  silently drift from the UI: `manage.py export_openapi_schema` writes the committed snapshot at
  `frontend/openapi.json`, `pnpm codegen` turns that into `src/api/schema.d.ts`, and `Backend CI`
  fails if the snapshot does not match the code.
