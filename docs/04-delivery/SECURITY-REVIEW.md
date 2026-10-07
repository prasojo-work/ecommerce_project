# Security review — NORDVIK API and web client

| | |
|---|---|
| **Consulted hat** | Cybersecurity |
| **Owner** | Founder |
| **Reviewed against** | commit `e3a0039` (M5 complete), working tree carrying the M6 changes |
| **Scope** | Phase 1 MVP — Django/DRF-less Ninja API (`backend/`), Next.js client (`frontend/src/`), local and deploy configuration |
| **Method** | full source read, OWASP Top 10 (2021) mapping, and targeted tests |
| **Status** | first pass complete; residual items listed in §5 |

## 1. Scope, method, limitations

This is a **source review plus targeted tests**, not a penetration test. There is
no DAST, no dependency-CVE triage against a live advisory feed, and no
infrastructure review — nothing is deployed yet (that lands in M7). Local Docker
Compose runs with `DJANGO_DEBUG=true`, so every production-only control in
`config/settings.py` is inert during local development and **unproven until the
first deploy**. Each finding below names the evidence and, where it was fixed, the
test that proves it.

## 2. Trust boundaries

Three boundaries matter:

1. **Browser → API.** The only caller we do not control. Every mutation, and every
   read of another user's data, must be authorised on the request itself.
2. **API → database.** A single Postgres. All access goes through the ORM, so
   injection is not a live concern unless raw SQL is introduced.
3. **Operator → Django admin.** A second, privileged surface, mounted at
   `/admin/` (`config/urls.py`), reachable with only a session cookie.

The mock payment provider runs in-process (`orders/payments.py`), so it is *not*
a boundary — but it keeps the shape of a real provider so nothing is re-plumbed
later.

## 3. Controls verified as sound

No finding, recorded so a later reader does not re-litigate them:

- **Error envelope.** `core/errors.py` maps every `HttpError` and validation
  failure to `{detail, code, errors, request_id}`. A validation failure is
  flattened to `field → message` so the client never renders `[object Object]`.
  Status codes are pre-mapped, including `429 → rate_limited`.
- **Request correlation.** `core/middleware.py` assigns every request an id,
  echoes it as `X-Request-ID`, and accepts a caller-supplied id **only when it
  parses as a UUID** — a malformed value is discarded rather than logged, which
  closes log-injection via the header. Covered by
  `core/test_observability.py::test_a_bogus_request_id_is_replaced_rather_than_trusted`
  (parameterised with `../../etc`, a SQL fragment, and a bare integer).
- **Structured logs.** `core/logging.py` (`JsonFormatter`, `RequestIDFilter`) and
  the `LOGGING` block in `config/settings.py` emit one JSON object per line, each
  carrying the request id.
- **Password validators.** All four Django validators are configured
  (`AUTH_PASSWORD_VALIDATORS` in `config/settings.py`), so weak and
  user-similar passwords are rejected at registration.
- **Token storage on the client.** The access token is held in React state only
  (`frontend/src/lib/auth.tsx` — `useState`, never `localStorage`), and the
  refresh token is an httpOnly cookie
  (`REFRESH_COOKIE_NAME`, `REFRESH_COOKIE_SECURE`). A stored XSS therefore cannot
  lift a durable credential out of web storage, and the session is restored from
  the cookie on reload.
- **No injection surface observed.** All queries go through the ORM; no raw SQL,
  `extra()`, or string-built queries exist in the codebase.
- **Idempotent checkout.** `POST /orders` takes a client idempotency key and
  returns the existing order on replay, so a double submit does not double-charge
  the mock provider.

## 4. Findings

### 4.1 Index

| ID | OWASP | Finding | Severity | Status |
|---|---|---|---|---|
| SEC-FIND-1.1 | A02 Cryptographic Failures | Committed placeholder secret key boots cleanly | High | Fixed |
| SEC-FIND-3.1 | A04 Insecure Design / A07 Auth Failures | No rate limit on `register` / `login` | High | Fixed |
| SEC-FIND-5.1 | A05 Security Misconfiguration | Unhandled exceptions returned tracebacks | Medium | Fixed |
| SEC-FIND-7.1 | A09 Logging & Monitoring Failures | Auth success and failure are not audited | Medium | Open |
| SEC-FIND-5.3 | A05 Security Misconfiguration | No security headers on the web tier | Medium | Open — M7 |
| SEC-FIND-6.1 | A06 Vulnerable & Outdated Components | No dependency scanning in CI | Medium | Open |
| SEC-FIND-2.1 | A01 Broken Access Control | No separation of owner and operator identity | Medium | Accepted — M7 |
| SEC-FIND-1.2 | A02 Cryptographic Failures | JWT signing key coupled to `SECRET_KEY`, undocumented | Low | Fixed |
| SEC-FIND-1.3 | A02 Cryptographic Failures | Passwords hashed with PBKDF2, not Argon2id | Low | Open |
| SEC-FIND-5.2 | A05 Security Misconfiguration | `DEBUG=true` in the local compose profile | Low | Accepted |
| SEC-FIND-7.2 | A09 Logging & Monitoring Failures | No error-tracking sink wired | Low | Open — M7 |

Category 4 (injection) produced no findings.

### 4.2 Details

#### SEC-FIND-1.1 — Committed placeholder secret key (High, Fixed)

**Evidence.** `config/settings.py` read `SECRET_KEY = env("DJANGO_SECRET_KEY")`.
A missing key already raised `ImproperlyConfigured` (django-environ, no default),
but `.env.example` ships `DJANGO_SECRET_KEY=change-me`, so a deploy that copied
the template booted successfully on a **public** key. That key signs the JWTs and
the session/CSRF cookies: an attacker could mint a valid access token for any
user id.

**Fix.** `config/settings.py` now routes the value through `require_real_secret_key`,
which refuses the literal placeholder with a message telling the operator how to
generate a real one.

**Proof.** `config/test_security_settings.py` — `test_placeholder_secret_key_is_refused`
and `test_a_real_secret_key_passes_through`.

**Residual.** The guard rejects only the exact shipped placeholder. A weak but
non-placeholder key chosen by an operator is out of scope; `.env.example` and the
deploy runbook (`ADR-0005`) both tell operators to generate 48 bytes of entropy.

#### SEC-FIND-3.1 — No rate limit on `register` / `login` (High, Fixed)

**Evidence.** `POST /auth/login` and `POST /auth/register` are anonymous and were
reachable without limit, so an attacker could brute-force a password list or
mass-register accounts at line speed.

**Fix.** Both endpoints carry an `AnonRateThrottle` (`accounts/api.py`) keyed on
the client address: login `10/5m`, register `30/h`, both settings-driven
(`THROTTLE_LOGIN_RATE`, `THROTTLE_REGISTER_RATE`). `NINJA_NUM_PROXIES` is set so
the key is the client address rather than the proxy's, which also stops a
per-IP limit from collapsing into a single global bucket.

**Proof.** `accounts/test_throttle.py` — `test_registration_is_throttled`.

**Residual.** Limits are per-process, in-memory: behind more than one API worker
the effective limit multiplies. Acceptable for the single-worker free tier; a
shared cache backend would be required before scaling out. Tracked in §5.

#### SEC-FIND-5.1 — Unhandled exceptions returned tracebacks (Medium, Fixed)

**Evidence.** With `DEBUG=true`, an unexpected exception in a handler rendered
Django's traceback page to the caller, exposing file paths, settings, and local
variables. Even in production, the default Ninja response body differed from the
documented envelope, so clients could not handle errors uniformly.

**Fix.** `core/errors.py` installs `HttpError` and `ValidationError` handlers that
return the documented envelope; `DEBUG` now defaults to **false**
(`DJANGO_DEBUG`), so an unset environment cannot leak a traceback page.

**Proof.** Covered indirectly by the API tests that assert on `detail` / `code` /
`errors`; the `DEBUG=false` default is asserted when importing settings.

#### SEC-FIND-7.1 — Auth events not audited (Medium, Open)

**Evidence.** No `logger` call exists in `accounts/` (grep for `logger` returns
nothing). A successful or failed login leaves no application-level record; a
brute-force attempt is visible only as a run of generic request log lines, with no
distinction between "wrong password" and "token rejected". The throttle fires at
`429`, which is a signal, but only after the threshold.

**Recommendation.** Add a single `logger.warning` on a failed authentication and
`logger.info` on success, both already carrying the request id via
`RequestIDFilter`. Cheap, and it makes the throttle observable.

**Why not fixed now.** It is a monitoring improvement rather than a vulnerability,
and pairing it with the error-tracking sink (SEC-FIND-7.2) in M7 avoids shipping
two logging changes.

#### SEC-FIND-5.3 — No security headers on the web tier (Medium, Open)

**Evidence.** `config/settings.py` sets HSTS, `X-Content-Type-Options`,
`Referrer-Policy`, and `X-Frame-Options` for the **API** responses. The Next.js
tier (`frontend/`) sets none of these, and the API's headers do not apply to a
document served from a different origin. A user reaching the app directly gets no
HSTS and no framing protection.

**Recommendation.** In M7 add a `headers()` block to `next.config.*` (HSTS,
`X-Content-Type-Options`, `Referrer-Policy`, `X-Frame-Options`) and set the same
`SECURE_*` intent at the host. A Content-Security-Policy is deferred until the
final asset origins are known, because a wrong CSP silently breaks the app.

#### SEC-FIND-6.1 — No dependency scanning (Medium, Open)

**Evidence.** CI (`.github/workflows/`) runs lint, type-check, and tests, but
nothing consults an advisory database, so a CVE in Django, Ninja, Next.js, or a
transitive package would go unnoticed until it was exploited or reported.

**Recommendation.** Add `pip-audit` (backend) and `npm audit --audit-level=high`
(frontend) as a non-blocking CI step first, then make the backend check blocking
once the tree is clean. Deferred because it needs a network fetch of the advisory
DB, which is not available in every build environment.

#### SEC-FIND-2.1 — No separation of owner and operator identity (Medium, Accepted)

**Evidence.** Every cart and order query scopes to `request.user`, so one customer
cannot read another's data — that part is correct. But the operator console
(`/admin/`) authorises on `is_staff` alone, and there is no second factor or
separate operator identity. A phished customer password does not grant admin, but
a phished **staff** password grants full order and catalogue control.

**Accepted for MVP.** The operator set is one person running their own store; a
second factor and a least-privilege operator role are M7 work. Recorded so it is a
decision, not an oversight.

#### SEC-FIND-1.2 — JWT signing key coupled to `SECRET_KEY` (Low, Fixed)

**Evidence.** `JWT_SECRET_KEY` defaulted to `SECRET_KEY` and was absent from
`.env.example`. Rotating the Django key would silently invalidate every issued
token, and the coupling was invisible to an operator.

**Fix.** `.env.example` documents `JWT_SECRET_KEY` with a generation command and a
rotation warning, and `settings.py` treats an *empty* value as unset
(`env("JWT_SECRET_KEY", default="") or SECRET_KEY`), so a stray `JWT_SECRET_KEY=`
cannot sign tokens with an empty secret.

**Proof.** Reading `settings.JWT_SECRET_KEY` with the variable set to `""` yields
`SECRET_KEY`, not `""`.

#### SEC-FIND-1.3 — PBKDF2 rather than Argon2id (Low, Open)

**Evidence.** `PASSWORD_HASHERS` is Django's default, so passwords use
PBKDF2-HMAC-SHA256. `docs/03-architecture/DATA-MODEL.md` described this as
"Argon2/PBKDF2", which was imprecise; the doc now states PBKDF2 and names Argon2
as the recommended upgrade.

**Recommendation.** `pip install argon2-cffi` and put `Argon2idHasher` first in
`PASSWORD_HASHERS`; Django rehashes each password on next successful login, so the
migration is gradual with no downtime.

**Why not fixed now.** Adding a dependency of this kind should be pinned and
verified with a real install rather than asserted in a review; and PBKDF2 with
Django's iteration count is not broken, only weaker than Argon2id against
GPU cracking. Accepted for the MVP.

#### SEC-FIND-5.2 — `DEBUG=true` in the local compose profile (Low, Accepted)

**Evidence.** `docker-compose.yml` and `.env.example` default to `DJANGO_DEBUG=true`
for local ergonomics.

**Accepted**, because the local profile is never exposed publicly and the default
for an unset environment is `false`. The risk is a copied `.env` reaching
production with debug on; the deploy runbook lists flipping this as a required
step, and `DJANGO_DEBUG` must be set explicitly in the host environment.

#### SEC-FIND-7.2 — No error-tracking sink (Low, Open — M7)

**Evidence.** `ARCHITECTURE.md` §11 calls for an "error tracking hook point".
Structured logs exist, but nothing ships them to a tracker, so an exception in
production is visible only to someone reading the host's log stream.

**Recommendation.** Wire the platform's log drain (Render) into a tracker, or add
a Sentry handler to the existing `LOGGING` dict at deploy time. Deferred to M7,
when there is a host to configure.

## 5. Residual and accepted risks

| Risk | Why it is still open | Revisit |
|---|---|---|
| Throttle counters are per-process | In-memory; multiplies across workers | Before scaling past one worker |
| Operator auth is password-only | Single-person store for the MVP | M7 |
| No dependency scanning | Needs a network advisory fetch in CI | M6 follow-up |
| No error tracker | No host exists yet | M7 |
| PBKDF2 instead of Argon2id | Dependency to be pinned and verified | M7 |
| Production settings unproven | Nothing is deployed | M7 |

## 6. Re-running the checks

```bash
# Backend unit + API + observability + throttle tests
cd backend && .venv/bin/python -m pytest -q

# Django's own production checklist (needs the production env values)
cd backend && DJANGO_DEBUG=false .venv/bin/python manage.py check --deploy

# Throttle, by hand: the 11th login attempt in the window must be a 429
for i in $(seq 1 11); do
  curl -s -o /dev/null -w '%{http_code}\n' -X POST "$API/api/v1/auth/login" \
    -H 'Content-Type: application/json' \
    -d '{"email":"nobody@example.com","password":"wrong"}'
done

# Frontend
cd frontend && npm run lint && npm run typecheck && npx vitest run
```
