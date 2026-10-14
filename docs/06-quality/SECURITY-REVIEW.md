# Security Review — LYSHEIM

> Consulted hat: **Senior Cybersecurity**. Owner: Founder.
> Status: **evidence produced** at `M6.3`, closing the design-stage pair. This is the other half of
> [`SECURITY-BASELINE.md`](SECURITY-BASELINE.md): that document names the assets, the threat model and
> the twelve findings; this one says what was built against each finding, what was run, and what the
> run reported. Every command in §7 was executed on 2026-10-14 against the committed tree. The things
> that do not pass are in §6, not smoothed over, and §8 lists what this review deliberately does not
> claim.

---

## 1. What this increment changed

Four controls, and only one of them was a case of tightening something that already existed.

| Control | Before | Now |
|---|---|---|
| `Content-Security-Policy` | absent from both applications | `core.middleware.ContentSecurityPolicyMiddleware` for the API and the console; `headers()` in `frontend/next.config.ts` for the storefront |
| Console sign-in throttling | no limit anywhere | `accounts.middleware.AdminLoginThrottleMiddleware`, reusing `AdminLoginRateThrottle` |
| The request id, readable by the browser | emitted on every response, invisible to JavaScript | `CORS_EXPOSE_HEADERS` |
| Dependency audit | none in CI | `pip-audit` and `pnpm audit --prod`, one failing CI step each |
| The secret guard | present in `prod.py`, asserted by nothing | `config.env.ensure_production_secret_key`, tested in both directions |

## 2. The findings, one row each

| Finding | Control the baseline requires | Evidence | Status |
|---|---|---|---|
| `SEC-FIND-1.1` token exposure | token-storage test; no token in `localStorage` | `M2.4`: the access token lives in memory only, one shared in-flight refresh, with the tests in `frontend/src/lib/` | Met |
| `SEC-FIND-1.2` IDOR | cross-user access returns `404`/`403` | `M2.6`/`M4.6`: ownership is the queryset, so another account's address or order is a `404` rather than a `403` that confirms the id | Met |
| `SEC-FIND-1.3` injection | no raw SQL; review of query call sites | ORM only — §7 records the search for `.raw(`, `.extra(`, `RawSQL` and `cursor()` coming back empty across the whole backend | Met |
| `SEC-FIND-1.4` XSS | CSP header present; axe/XSS review clean | new: a policy on both apps. React escaping throughout, no `dangerouslySetInnerHTML` anywhere, route audit 11/11 (`A11Y-PERF-REPORT.md`) | Met, with a residual — §6.2 |
| `SEC-FIND-1.5` secrets | secret-guard test; secret scan in CI | `ensure_production_secret_key` refuses the repository's key, tested both ways; `.env` gitignored with `!.env.example`; lockfiles committed | Met in part — §6.3 |
| `SEC-FIND-1.6` DoS / abuse | throttling tests return `429` | `M2.3` and after: auth, cart, orders and payments all throttled through `LiveRateThrottle`, rates in `NINJA_DEFAULT_THROTTLE_RATES`, `NINJA_NUM_PROXIES` pinned to the real topology | Met |
| `SEC-FIND-1.7` admin exposure | admin login throttled; account documented | new console throttle (§3.2); `RUNBOOK.md` §9 documents creating an operator and the `is_staff`/`is_superuser` difference | Met |
| `SEC-FIND-1.8` supply chain | audit commands exit clean | both wired as CI steps and both clean today — §5 | Met |
| `SEC-FIND-1.9` logging hygiene | log review contains no PII or secrets | `core/logging.py` renders one JSON line per record — level, logger, message, timestamp and the correlation id — and §7 records the review of every logger call site | Met |
| `SEC-FIND-1.10` transport & headers | header check on the deployed URL | `prod.py`: HSTS with subdomains and preload, `nosniff`, referrer policy, secure cookies, TLS redirect with the proxy header; `check --deploy` reports no warnings under production settings (§4); verified against the live URL at `M2.7` | Met |
| `SEC-FIND-1.11` cross-origin refresh | cross-origin refresh rejected without an origin | `ADR-0009`'s origin guard answers `403` before it reads the cookie, pinned in `test_accounts_api.py` | Met |
| `SEC-FIND-1.12` cart cookie tampering | closed by `ADR-0017` | the surface no longer exists: the cart requires a bearer token, so there is no cookie to tamper with | Closed |

## 3. The controls that needed code

### 3.1 One policy in settings, two in practice

`SECURITY-BASELINE.md` §6 names the policy it wants — `default-src 'self'; img-src 'self' data:;
`object-src 'none'` — and three documents then say how to get it: finding `SEC-FIND-1.4` in that
baseline, `PLAN.md`'s framework choices and `ARCHITECTURE.md`'s cross-cutting concerns each call it a
**Django 6 built-in**. **It is not.** Django ships no CSP support at all — there is no setting to turn
on and no header to configure — and all three claims are corrected alongside this review rather than
left for a reader to find. That left a choice between a dependency (`django-csp`) and a header; one
middleware and one setting is the smaller thing to own, and it keeps the policy where the project keeps
the rest of its policy (`ADR-0011`).

Three directives were added to the baseline's list, each closing a specific gap rather than padding:
`base-uri 'self'` stops an injected `<base>` from re-pointing every relative URL on the page,
`frame-ancestors 'none'` is what replaced `X-Frame-Options` for browsers that ignore the old header,
and `form-action 'self'` keeps a form on a page we served from posting an address somewhere else.

**The console needs a second policy, and that is a deliberate exception.** Django's own admin templates
bring inline `<script>` and `style` attributes, so under the strict policy the console renders as
unstyled, dead markup — which is not a security posture, it is an outage. `CONTENT_SECURITY_POLICY_ADMIN`
therefore adds `'unsafe-inline'` to exactly two directives and keeps every origin restriction: nothing
loads from another host and nothing may frame it. The narrowness is asserted rather than described —
subtracting the strict policy from the console's leaves precisely those two directives, so a third one
appearing later is a visible change in review instead of a silent widening.

The API's own responses are JSON, where a policy is inert either way. They get the strict one, which
costs nothing and is what any accidental HTML response from that service would inherit.

### 3.2 The console's sign-in had no limit at all

`SEC-FIND-1.7` is High priority and calls the console "the highest-value target". Its control reads
"admin login throttled" — and the console's sign-in was, in fact, the only screen in this system with
no limit on it. Ninja attaches throttles to Ninja operations, and `/admin/login/` is a plain Django
view, so every rule in `NINJA_DEFAULT_THROTTLE_RATES` stopped short of the one page where a guessed
password buys the entire catalog and every order in it.

`accounts/middleware.py` attaches `AdminLoginRateThrottle` — the same `LiveRateThrottle` the auth
endpoints use, reading the same rates mapping, keyed on the client by the same rules — to that view. No
second implementation of the window exists, so the console's limit cannot drift away from the API's.
Three decisions are worth recording because each would be a defect the other way round:

- **Keyed on the client, not the submitted username.** Keyed on the account, this would be a way to lock
  a known operator out of the console instead of a way to slow an attacker down. A test asserts that
  changing the name in the form does not buy a fresh window.
- **Only `POST` is counted.** A `GET` is somebody looking at a form, and counting it would spend an
  operator's budget on a browser refresh — the back button as a lockout.
- **The refusal says when to come back.** `429` with a `Retry-After` of at least one second, because a
  bare `429` leaves the client guessing, and guessing wrong makes the block longer.

### 3.3 The request id was emitted and invisible

`NFR-5` says correlation ids cross the API and the web app. The server has been emitting `X-Request-ID`
on every response since `M0.5`, and the envelope has carried it since `M1` — but a response header is
readable from JavaScript only when CORS names it, so from the browser's side the correlation was
one-sided: the id was in the log and in the body, and not in the one place a client-side error handler
could reach. `CORS_EXPOSE_HEADERS = ["X-Request-ID"]` closes that, and it grants nothing new — the same
id is already in the error body (`API.md` §3).

### 3.4 The dependency audit

`SECURITY-BASELINE.md` §9 already named the commands and nothing ran them. They are now CI steps in the
jobs they belong to: `uv run pip-audit` in `backend.yml`, `pnpm audit --prod` in `frontend.yml`. Both
fail the job rather than warn, because an advisory nobody is obliged to act on is a log line and not a
control. `--prod` on the frontend side on purpose: the dev dependencies are this repository's own build
tooling and not something the storefront ships to anybody.

### 3.5 The secret guard

The guard existed — `prod.py` refused to start on the repository's development key — and nothing
asserted it. The obvious test ("does importing `prod` fail?") is the wrong one: in a test environment
with `DJANGO_SECRET_KEY` unset the import is exactly what raises, so the test would pass for a reason
that has nothing to do with the guard, and fail outright on a machine whose `.env` sets a real key. The
check moved to `config.env.ensure_production_secret_key`, which takes the value as an argument, and both
directions are asserted: the repository's key raises, a generated one is accepted.

## 4. `manage.py check --deploy`, under production settings

Run with `DJANGO_SETTINGS_MODULE=config.settings.prod`, a 128-character random key and a non-empty
`DJANGO_ALLOWED_HOSTS`:

```
SystemCheckError: System check identified some issues:

ERRORS:
?: (mail.E001) Your MAILERS setting uses a development-only email backend in the 'default' entry
        (django.core.mail.backends.dummy.EmailBackend).

System check identified 1 issue (0 silenced).
```

**One error, zero warnings.** No `security.W*` check fails: HSTS, the TLS redirect, the proxy header,
secure cookies, `nosniff`, the referrer policy, `X_FRAME_OPTIONS` and the secret key all pass. The
single error is a deliberate design decision, not an oversight, and it is in §6.1.

(For the record: run against the development settings — which is what `SECURITY-BASELINE.md` §9's
unqualified command does — the same check reports the transport warnings, because those settings turn
those controls off so that a local plain-HTTP request is not redirected to a TLS port nothing is
listening on. The useful run is the production one above.)

## 5. Dependency audits

| Command | Result |
|---|---|
| `uv run pip-audit` | `No known vulnerabilities found` |
| `pnpm audit --prod` | `No known vulnerabilities found` |

Both are pinned in CI, so a future advisory fails the build rather than being discovered later.

## 6. Known and accepted deviations

### 6.1 The production mailer is `dummy`, and `check --deploy` says so

`M4.4` (`ADR-0010`) mocks the email transport, and production uses `dummy` rather than `locmem` so that
a long-lived web process does not accumulate one unsent message per order forever. `check --deploy`
flags that, correctly, as a development-only backend. **Accepted:** there is no transport to send
through, and the alternative — `locmem` in production — trades a check error for an unbounded memory
leak. It becomes a real finding the day a real transport exists, and that is `M7`'s or the data track's
work rather than something to paper over here.

### 6.2 `script-src 'unsafe-inline'` on both applications

Next.js streams an inline bootstrap script into every document, and a nonce cannot be produced by
`headers()` in `next.config.ts` — that config is evaluated per build, not per request. So the choice is
that concession or a storefront that does not hydrate. The directive still carries real weight: no
third-party origin can serve a script into this app, which is the injection route that matters most.
**Residual, not closed.** Moving to a per-request nonce through middleware is the next step, and calling
the XSS finding fully met on a policy with `'unsafe-inline'` in it would be overstating this.

### 6.3 There is a secret guard, and there is no secret scanner

`SEC-REMEDIATE-1.5`'s validation column asks for two things: a secret-guard test, and a secret scan in
CI. The guard is built and tested (§3.5). The **scan is not wired** — §9's own command list does not
include one, and this increment did not add a scanning action. What stands in its place today is the
guard, `.env` excluded from git with `!.env.example` as the only committed sample, and lockfiles
committed. That is weaker than a scanner, and the honest place to say so is here rather than in a
checklist box.

### 6.4 Rate limits are per-process

The windows live in the process cache, so an operator running several workers multiplies every limit in
`NINJA_NUM_THROTTLE_RATES` by the number of processes. The deployment is a single `uvicorn` process
(`RUNBOOK.md` §7.8), which is why this is acceptable at v1 and why the throttle key resolution had to
be pinned to the real proxy count in the first place. A shared cache is the fix if that changes.

## 7. Verification commands, and what they reported

| Command | Reported |
|---|---|
| `uv run ruff format --check .` · `uv run ruff check .` | clean |
| `uv run basedpyright` | 0 errors |
| `uv run pytest --cov` | 356 passed, coverage gate (`fail_under = 80`) green |
| `uv run python manage.py check` | no issues |
| `manage.py check --deploy` (production settings) | 1 error, 0 warnings — §4 |
| `uv run pip-audit` | no known vulnerabilities |
| `pnpm audit --prod` | no known vulnerabilities |
| `grep -rn "\.raw(\|\.extra(\|RawSQL\|cursor()" backend --include=*.py` | no matches — `SEC-FIND-1.3` |
| `grep -rn "logger\.[a-z]+\(" backend --include=*.py` | one call site — `core/errors.py` logs the request path and the exception on an unhandled error, and neither carries a credential nor a PII field — `SEC-FIND-1.9` |
| `pnpm typecheck` · `pnpm lint` · `pnpm format:check` · `pnpm test` · `pnpm build` | clean; 163 tests |
| `pnpm audit:routes` | 17 passed — 11 routes at WCAG 2.1 AA, 6 performance budgets (`A11Y-PERF-REPORT.md`) |
| `curl -sI` on the built storefront and the API | the policies in §3.1, as configured |
| a Chromium probe per route: mark `window`, follow an in-app link, count CSP violations | `hydrated: true` on all four routes, 0 violations, and one genuinely cross-origin `fetch` refused — §3.1 |

## 8. What this review does not claim

- **No pen-testing, no exploit development, no attack tooling.** That exclusion is the baseline's policy
  (§1) and it still holds; nothing here was validated by breaking in.
- **No claim about the deployed environment's headers.** Those were verified at `M2.7` and are the
  subject of the post-deploy check in §9 of the baseline. The header work in this increment was
  verified on the built application locally, and a `curl` of the live URL is `M7`'s checklist item.
- **No claim that the CSP is final.** §6.2 is the residual, and it is the one place where a reader
  should read "Met" as "met for a demo, with the next step named".
- **No claim about operator behaviour.** The console is throttled and documented; whether one operator
  or five share an account, and what happens when one leaves, is a process question `RUNBOOK.md` §9
  describes rather than enforces.
