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

Auth endpoints are **rate-limited**; a 429 returns `Retry-After`.

## 3. Error envelope

Every error response uses one shape (see `NFR-4`):

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Email is already registered.",
    "details": [{"field": "email", "issue": "duplicate"}],
    "request_id": "01J9Z3K8Q2M4"
  }
}
```

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

Listing responses are paginated: `{ "items": [...], "page": 1, "page_size": 24, "total": 137 }`.

## 5. Cart (guest or authenticated)

The cart is resolved by the authenticated user, or by a signed `cart` cookie for guests.
On login, a guest cart is **merged** into the user cart (`ADR-0008`).

| Method | Path | Purpose |
|---|---|---|
| GET | `/cart` | Current cart with line items and totals |
| POST | `/cart/items` | Add `{variant_id, quantity}` |
| PATCH | `/cart/items/{id}` | Set `{quantity}` (stock-capped) |
| DELETE | `/cart/items/{id}` | Remove a line |

`409` is returned when a requested quantity exceeds available stock.

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

| Method | Path | Purpose |
|---|---|---|
| GET | `/addresses` | List |
| POST | `/addresses` | Create |
| PATCH | `/addresses/{id}` | Update |
| DELETE | `/addresses/{id}` | Delete |

## 9. Operations

| Method | Path | Purpose |
|---|---|---|
| GET | `/healthz` | Liveness/readiness for uptime checks (no auth, no DB models) |

The operator console is **Django admin** (`/admin/`), not part of this REST API (`ADR-0007`).

## 10. OpenAPI

- The schema is generated at `/api/v1/openapi.json` and a browsable UI at `/api/v1/docs`.
- The frontend's API client types are generated from this schema, so the contract cannot
  silently drift from the UI.
