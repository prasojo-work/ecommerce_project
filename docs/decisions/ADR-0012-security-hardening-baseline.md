# ADR-0012: Security hardening — one error envelope, correlation ids, and in-process rate limiting

- **Status:** Accepted
- **Date:** 2026-10-07
- **Deciders:** Founder
- **Related:** `ADR-0003`, `ADR-0004`, `RISK-5`, `SECURITY-REVIEW.md`

## Context

M6 requires an OWASP Top 10 pass over the MVP (`ROADMAP.md` → `PLAN-1.7`). The review
(`SECURITY-REVIEW.md`) found three things the API could not answer for:

1. **Failures were unshaped.** Ninja returns only `detail` for an `HttpError` and puts a *list* in
   `detail` for a validation failure, so the client rendered `[object Object]`. `ARCHITECTURE.md`
   §5 already documented a `{detail, code, errors}` envelope that nothing implemented.
2. **Nothing was traceable.** `ARCHITECTURE.md` §11 calls for logs with a request id; there were
   plain-text logs with none, so a user's report could not be tied to a request.
3. **Anonymous endpoints were unlimited.** `POST /auth/login` and `/auth/register` could be called
   at line speed, so password brute-forcing and mass registration were both trivial
   (`SEC-FIND-3.1`).

Each had more than one reasonable answer, and the answers have different costs. This records the
choices and, importantly, what each one gives up.

## Options considered

**Error shape** — (a) accept Ninja's defaults and teach the client to cope; (b) adopt a
DRF-style exception handler wholesale; (c) register explicit handlers on the `NinjaAPI`.

**Request id** — (a) log without one; (b) generate a fresh id per request and always ignore the
caller's; (c) accept a caller-supplied id, but only when it parses as a UUID.

**Rate limiting** — (a) `django-ratelimit` decorators; (b) Ninja's throttles backed by a shared
cache (Redis/Upstash), so counters are global; (c) Ninja's in-process throttles with per-endpoint
rates held in settings.

## Decision

- **Error shape — option (c).** `core/errors.py` installs handlers for `HttpError` (which already
  covers `Throttled`) and `ValidationError`, mapping statuses to stable codes and flattening a
  validation failure to `field → message`. The envelope carries `request_id` when available.
- **Request id — option (c).** `core/middleware.py` trusts an inbound `X-Request-ID` **only** when
  it parses as a UUID and otherwise generates one. An unvalidated header would be a log-injection
  vector — newlines and arbitrary text straight into the log stream — so a malformed value is
  replaced, never echoed. The id is returned in `X-Request-ID` and attached to every log line via a
  `ContextVar` and a `logging` filter (`core/logging.py`).
- **Rate limiting — option (c) for the MVP.** Anonymous limits live in settings
  (`THROTTLE_LOGIN_RATE` = `10/5m`, `THROTTLE_REGISTER_RATE` = `30/h`) and are applied per endpoint
  in `accounts/api.py`. `NINJA_NUM_PROXIES` is set so the key is the client address, not the proxy's.
- **Secrets fail fast.** Settings refuse to start when `SECRET_KEY` is still the `.env.example`
  placeholder (`SEC-FIND-1.1`), rather than trusting the operator to notice.

## Consequences

- **Positive:** one error shape across the API, so the client has a single failure path; every
  response and log line is correlatable to a request id that is safe to echo; brute-force and mass
  registration are bounded; and the two commonest "forgot to configure it" mistakes (placeholder
  key, debug left on) fail closed instead of open.
- **Negative / costs:** the throttle counters are **per process and in memory**, so behind *n*
  workers the effective limit is *n*× the configured rate, and a restart clears them. This is
  accepted for a single-worker free tier and recorded as a residual risk. The error envelope is a
  bespoke handler, so Ninja upgrades may need it revisited.
- **Follow-ups:** move throttle counters to a shared cache before running more than one API worker.
  Add an auth-event log line so the throttle is observable (`SEC-FIND-7.1`). Add the web tier's own
  security headers (`SEC-FIND-5.3`).

## Reversibility

**Two-way door.** Every piece is a small module behind a stable interface — the handlers are
registered in one place, the middleware is a standard Django middleware, and the limits are
settings. Swapping in a shared-cache throttle or a third-party error handler would not touch the
domain apps.
