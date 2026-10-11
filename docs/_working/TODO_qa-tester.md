# TODO — QA (`qa_tester`)

**Scope:** the account surface as it stands after `M2.6` — `accounts.User`, `accounts.Address`,
`accounts.RefreshToken`, the five auth endpoints `POST /auth/register`, `POST /auth/login`,
`POST /auth/refresh`, `POST /auth/logout`, `GET /auth/me`, plus `PATCH /auth/me` and the five
`/addresses` routes (`SCOPE.md` `US-2.1`–`US-2.5`, `ADR-0009`, `API.md` sections 2 and 8).

**Status legend:** `[x]` executed, with the observed result recorded · `[ ]` **Not run**, with the
reason. Nothing below is marked passed without an observed result, and nothing is copied from the
implementation's own claims.

## QA-PLAN — strategy

Auth is the highest-risk surface in this project: it is the only place where a defect is a security
incident rather than a display problem. Four properties are worth defending, and the cases below are
grouped by them rather than by endpoint.

- **Identity** — only the right person gets in, and the account that comes back is the one the token
  names.
- **Revocation** — a session can be ended, and ended *for real*, not just in the browser.
- **Non-disclosure** — failures must not reveal which addresses have accounts, and credentials must not
  appear anywhere they are not needed.
- **Scoping** — a credential is good only for the operation it was minted for.

**Levels.** 50 auth contract tests (`backend/tests/test_accounts_api.py`, 14 added at `M2.3` and 6 at
`M2.6`), 24 address tests (`test_addresses_api.py`, `M2.6`), 20 model tests
(`test_accounts_models.py`), 5 cross-origin tests (`test_cors.py`, `M2.4`), 99 frontend unit tests
(`vitest`: 12 for the session store, 17 for the address form's rules, 12 for the failure envelope),
and a scripted end-to-end pass over real HTTP — because
cookie attributes, headers and rate limits cannot all be verified through the test client alone. A
throttle lives in the process's own cache and CORS headers on the response path, so neither can be
exercised from outside the process. `pytest` is **181 tests**. `M2.1`–`M2.3` were run on SQLite and
then on PostgreSQL 17.11; from `M2.4` on, the suite runs against PostgreSQL directly, because that is
the engine that serves production and the two differ in exactly the place that matters (see
`QA-C30`).

**Deliberately not tested.** JWT signing internals and password hashing internals (libraries' jobs, not
ours), TLS and transport hardening (`M7`).

**Blocked, not skipped.** Two groups wait on things that do not exist yet: `QA-C43`–`QA-C51` and
`QA-C56`–`QA-C62`, the sign-in, registration, session and account behaviour driven in a *real
browser* (every screen involved exists now; what is missing is a browser, not a back end), and
`QA-C28`, cross-site cookie delivery with `SameSite=None`, which needs a second real origin and
therefore `M7`. The remainder has been run, on PostgreSQL — the browser cases are the gap, not a hole
in the plan.

## QA-CASE — cases and observed results

### Identity

- [x] `QA-C1` Register returns `201` with an access token, `token_type`, `expires_in` and the account.
      **Observed:** `201`; `expires_in: 900`; body carries no password field.
- [x] `QA-C2` A mixed-case, whitespace-padded address is stored lower-cased.
      **Observed:** `"  M22.Check@Example.COM "` → `m22.check@example.com`.
- [x] `QA-C3` Sign-in is case-insensitive. **Observed:** `M22.CHECK@example.com` → `200`.
- [x] `QA-C4` A duplicate address is refused. **Observed:** `400`, `VALIDATION_ERROR`, `details`
      naming `body.email`; a case-variant duplicate is refused the same way.
- [x] `QA-C5` A weak password is refused with every applicable reason.
      **Observed:** `12345` → `400` with three details: too short, too common, entirely numeric.
- [x] `QA-C6` A password derived from the account's own address is refused (similarity validator).
      **Observed:** `ada@example.com` / `ada@example.com` → `400`, `body.password`.
- [x] `QA-C7` An inactive account cannot sign in. **Observed:** `401`.
- [x] `QA-C8` `GET /auth/me` returns the token holder, and only the token holder's fields.
      **Observed:** `200` with `{id, email, display_name, is_staff}`; no password key.

### Revocation

- [x] `QA-C9` A refresh rotates the credential. **Observed:** the cookie value changed and the previous
      row is revoked; exactly one live token remains.
- [x] `QA-C10` Replaying a rotated token is detected and ends every session.
      **Observed:** `401`; live tokens for that user fell to **0**.
- [x] `QA-C11` Logout answers `204`, clears the cookie and ends the session server-side.
      **Observed:** `204`; `Set-Cookie` with an empty value; replaying the pre-logout token → `401`.
- [x] `QA-C12` Logout is idempotent when the cookie is unreadable. **Observed:** `204`.
- [x] `QA-C13` Logout without an access token is refused. **Observed:** `401`.
- [x] `QA-C14` Deleting a user removes their tokens (cascade). **Observed:** token count fell to `0`.

### Non-disclosure

- [x] `QA-C15` A wrong password and an unknown address are indistinguishable.
      **Observed:** identical `code` and `message` over HTTP, not merely in tests.
- [x] `QA-C16` The refresh token never appears in a response body.
      **Observed:** the cookie's exact value does not occur anywhere in the registration response JSON.
- [x] `QA-C17` The refresh cookie is `HttpOnly` and scoped. **Observed:**
      `HttpOnly; Path=/api/v1/auth; SameSite=Lax; Max-Age=1209599`.
- [x] `QA-C18` The cookie is `Secure` when production settings ask for it. **Observed:** flag present
      under `REFRESH_COOKIE_SECURE=True`.

### Scoping

- [x] `QA-C19` An access token is refused by `/auth/refresh`. **Observed:** `401`.
- [x] `QA-C20` An expired access token is refused; `typ` and `sub` are required claims.
      **Observed:** `401` with a negative TTL; `TokenError` when the type is swapped.
- [x] `QA-C21` An unsigned or malformed token is refused. **Observed:** `401`.
- [x] `QA-C22` Missing credentials on a protected route answer `401` in the standard envelope.
      **Observed:** `401`, `UNAUTHENTICATED`, with a `request_id`.

### Regression

- [x] `QA-C23` The catalog is unaffected by auth. **Observed:** `GET /products` and `GET /credits`
      → `200`; 46 products still present after the migration and after the test account was removed.
- [x] `QA-C24` No server-side errors during the whole flow. **Observed:** 0 tracebacks, 0 `500`s.
- [x] `QA-C25` The contract documents the new routes. **Observed:** all five `/api/v1/auth/*` paths in
      the regenerated `frontend/openapi.json`; the frontend typechecks and lints against it.

### Cross-origin access in the browser (`M2.4`)

- [x] `QA-C38` A preflight for `POST /auth/refresh` succeeds. **Observed:** `OPTIONS` with
      `Origin: http://localhost:3000` answered `200`, echoing the origin, with
      `access-control-allow-credentials: true`, `POST` among the allowed methods and `content-type`
      among the allowed headers.
- [x] `QA-C39` A preflight for an authorised call allows `authorization`. **Observed:**
      `access-control-allow-headers` carries `authorization`, so the bearer header the interceptor
      sends is not blocked before the request is even made.
- [x] `QA-C40` A registration from the storefront origin is readable and sets the cookie.
      **Observed:** `201` with the allow-origin and allow-credentials headers, and exactly one
      `lysheim_refresh` cookie set.
- [x] `QA-C41` The silent refresh rotates the cookie over CORS. **Observed:** `POST /auth/refresh`
      with the cookie and the storefront origin answered `200`, echoed the origin, and rotated exactly
      one refresh cookie.
- [x] `QA-C42` An unlisted origin gets no access, and the API's own guard refuses it too.
      **Observed:** the call with `Origin: https://evil.example` came back with **no**
      `access-control-allow-origin` header — so a browser refuses to expose the response even though
      the API answered — while `POST /auth/refresh` from that origin answered `403` `FORBIDDEN` from
      the origin guard. The two layers are independent, which is exactly why both are checked.
- [ ] `QA-C43` **Not run — `M2.5`.** The interceptor in a real browser: sign in, drop the access token
      (or wait it out), and confirm a protected call renews silently and retries with nothing visible
      to the customer. It needs a page that makes authenticated calls, which `M2.5` provides. The
      JavaScript is covered by unit tests today — 12 in `src/lib/session.test.ts`, including the
      single-refresh guard — but "the browser does the right thing with these headers" is precisely
      what a unit test cannot claim.

### Everything else

- [x] `QA-C26` Rate limiting: `N` failed logins within a window produce `429` with `Retry-After`.
      **Observed:** the eleventh attempt answered `429` — exactly the configured `10/min` — in the
      standard envelope with the `RATE_LIMITED` code, a `request_id`, and `Retry-After: 51` in whole
      seconds. The *correct* password was refused as well, because the limit is on the endpoint rather
      than on failures.
- [x] `QA-C27` `/auth/refresh` from a foreign `Origin` is refused. **Observed:** `403` `FORBIDDEN`,
      "That request did not come from this storefront." A foreign `Referer` with no `Origin` is refused
      too, and a request carrying neither is allowed through, because that is a non-browser client.
- [ ] `QA-C28` **Not run — blocked to `M2.4`.** Cross-site cookie delivery with `SameSite=None; Secure`
      from a browser origin; requires the frontend session work and a second origin.
- [x] `QA-C29` The suite and the full flow on PostgreSQL, the engine that serves production.
      **Observed:** `uv run pytest -q` → **132 passed** against `test_lysheim` on PostgreSQL 17.11;
      `migrate` and `seed` both ran clean, and the seeded counts match SQLite exactly (7 categories,
      46 products, 95 variants, 46 images, 46 credits). The auth flow re-run over HTTP behaved
      identically to SQLite at every step, with 0 tracebacks and 0 `500`s. Schema facts checked
      directly in `psql`: `accounts_refreshtoken.jti` carries a real UNIQUE constraint, `revoked_at`
      is nullable, no column holds the token itself, and the default-address rule is a genuine partial
      index — `CREATE UNIQUE INDEX unique_default_address_per_user ON accounts_address USING btree
      (user_id) WHERE is_default`.
- [x] `QA-C30` Concurrent refresh with one credential. **Observed:** the row lock serialises the two
      requests, and it was measured rather than assumed — with one process holding `SELECT ... FOR
      UPDATE` on the token row for 5s, `rotate()` blocked **3.52s** and returned only after the holder
      committed. On SQLite the same call cannot be blocked at all, because Django does not apply the
      clause. Consequence, observed end to end: `refresh A: 401 | refresh B: 200`, leaving **0** live
      tokens. Exactly one request wins, the loser is read as reuse, and reuse revokes everything —
      including the winner's new token. See `QA-G4`.
- [x] `QA-C31` Address ownership: user A must not read, edit or delete user B's address. **Observed:**
      user B's book came back `[]`, and `PATCH` and `DELETE` against A's address id both answered `404`
      `NOT_FOUND` ("No such address.") rather than `403` — a `403` would have confirmed the id exists,
      which is the whole point of trying. A's two rows were then read back and were unchanged, so the
      refusals did nothing as well as said nothing. The same property is asserted at every level in
      `test_addresses_api.py`: unlisted, un-editable, un-deletable, and unchanged afterwards.
- [x] `QA-C32` `PATCH /auth/me` for the display name (`US-2.4`). **Observed:** the endpoint is in
      `API.md` §2 now and answers `200` with the updated profile; a body carrying only `display_name`
      changes only that field, the value is trimmed, and an **empty body** leaves the name alone rather
      than clearing it — the behaviour that matters, because a client sending `{}` by accident must not
      erase the customer's name.
- [x] `QA-C52` The default-address rule, end to end. **Observed:** the first address is stored
      `is_default: true` without being asked for it, a second is `false`, promoting the second leaves
      **exactly one** default and moves it to the front of the list, deleting the default promotes the
      oldest survivor, and clearing the default outright is refused `409` `CONFLICT` — a conflict
      rather than a `400`, so the frontend will not hang that sentence on a form field.
- [x] `QA-C53` A field error reads the same however it was produced. **Observed:** a
      pydantic-generated body error names `body.recipient` and one raised by hand names `body.email`,
      from the same endpoints. Before the fix the first arrived as `body.payload.recipient`; a client
      stripping the view prefix as `API.md` §3 instructs would have matched one shape and fallen back
      to a form-level message for the other. See `QA-B5`.

### The account screen (`M2.6`)

- [x] `QA-C54` `/account` serves without a session, and the server's HTML carries the *restoring*
      state rather than the signed-out one. **Observed:** `GET /account` answered `200` (7761 bytes)
      with `<title>Your account — LYSHEIM</title>` and exactly one `<h1>`; the HTML carries the
      loading state and does **not** carry the signed-out copy — the flash that would otherwise hit a
      signed-in customer on every navigation, which is the whole reason `M2.4` has a three-state
      model. Neither session-bound section is in the server HTML: 0 `<h2>` elements, and both section
      ids absent. **The check itself was wrong before it was right.** It searched for the words
      "Profile" and "Addresses", which the page's own meta description contains in prose, so it
      reported two rendered sections that were not there. It matches by section id now. A check that
      passes for the wrong reason is worth less than one that fails.
- [x] `QA-C55` The payloads the forms build are the payloads the API accepts. **Observed:** a body
      carrying `postal_code` and `is_default` exactly as `toCreatePayload` builds it answered `201`,
      and the first address came back `is_default: true` without being asked; the `PATCH` shape from
      `toUpdatePayload` — which carries no `is_default` key at all — answered `200` and left the
      address default; `PATCH /auth/me` with `display_name` answered `200`. A field-name mismatch
      between a form and the contract is invisible to `tsc` wherever the body is typed as the
      generated schema, so the wire is worth asking directly.
- [ ] `QA-C56` **Not run — needs a browser.** Signing in lands on `/account`, not the home page.
- [ ] `QA-C57` **Not run — needs a browser.** Saving the profile form changes the name the header
      shows, with no reload. Both read one store; this is what would catch them drifting apart.
- [ ] `QA-C58` **Not run — needs a browser.** Adding an address: the first becomes the default without
      being asked, a later one only when the box is ticked, and `Default` appears as a word rather
      than as a colour (`NFR-2`).
- [ ] `QA-C59` **Not run — needs a browser.** Editing: the form opens holding that address's values,
      switching to another row replaces them rather than leaving one address's text in another's
      inputs, and saving does not clear the default.
- [ ] `QA-C60` **Not run — needs a browser.** A rejected field error appears beside its own input — a
      postal code past 32 characters — with `aria-invalid` and `aria-describedby` pointing at it, and
      a submit with a required field blank never leaves the browser.
- [ ] `QA-C61` **Not run — needs a browser.** Removing asks first, and once the default is removed the
      surviving address is shown as the default.
- [ ] `QA-C62` **Not run — needs a browser.** `/account` while signed out says so and offers a way to
      sign in, rather than showing an empty account.

## QA-BUG — defects found and their state

- [x] `QA-B1` **Fixed, found by test.** Every auth route answered `404`. The router was mounted at
      `/auth` *and* each route declared `/auth/...`, so the real paths were `/api/v1/auth/auth/...`.
      Severity: blocking. Caught by the first run of the contract tests, which is what they are for.
- [x] `QA-B2` **Fixed, found by test.** A `401` from `/auth/refresh` did not clear the refresh cookie.
      Ninja's exception handler builds a fresh response, so a cookie cleared on the injected response
      and then abandoned by a `raise` never reached the client — leaving the browser to re-present a
      dead token on every page load. Severity: medium (no leak, but an unrecoverable client state).
      Fixed by returning the response instead of raising.
- [ ] `QA-B3` **Open, cosmetic.** Missing or malformed credentials on a Ninja-protected route return
      the library's `"Unauthorized"` rather than the project's own wording, so the message differs from
      the hand-written `401`s elsewhere. Not misleading, but inconsistent.
- [ ] `QA-B4` **Open, risk.** `JWT_SECRET_KEY` falls back to `DJANGO_SECRET_KEY`. Rotating the cookie
      signing key therefore requires rotating the application secret as well, and vice versa. Acceptable
      for this deployment, worth an explicit pair of secrets when `M7` sets production variables.
- [x] `QA-B5` **Fixed, found by test.** `M2.6`. One contract carried two shapes of field error:
      pydantic's own errors arrived with the view parameter in the path (`body.payload.country`) while
      errors raised by hand produced `body.email`. Severity: medium — a client following `API.md` §3
      would silently lose field-level placement for exactly the errors the *schema* generates, which are
      the common case, while the hand-written ones kept working. It survived because every field-error
      test until then asserted a hand-raised error, so no test had ever inspected a pydantic one. Fixed
      in `core/errors.py` by dropping the view parameter's name from the reported location; a test now
      pins both paths to the same shape.

## QA-GAP — questions for the product owner

> **Deferred by founder decision (2026-10-12).** `QA-G3`, `QA-G4`, and `QA-G7` are accepted as they
> stand for Phase 1: each has a safe default already shipped, none of them blocks an increment, and
> the founder has asked that they not be advanced further now. They stay recorded so the reasoning
> survives, but no work should be raised against them while the store is being built — do not
> re-propose the cross-tab lock, the split sign-in copy, or the validator ordering.

- [ ] `QA-G1` `ADR-0009`'s refresh-logout row is satisfied, but a token revoked by *logout* takes the
      reuse-detection path on replay, which is conservative and a no-op. Should logout-marked tokens be
      distinguished from reuse-marked ones so the audit trail can tell an expired session from a
      suspected compromise?
- [ ] `QA-G2` No retention or cleanup exists for `refresh_token` rows; nothing is deleted on expiry. Is
      that acceptable, or should `M2.3` add a purge?
- [ ] `QA-G3` Is one message for all sign-in failures the intended UX, or does `UX.md` want the specific
      "no account with that address" copy? Security favours the single message; the microcopy listed in
      the spec may say otherwise.
- [ ] `QA-G4` Two tabs refreshing at the same moment log the user out. The lock makes the outcome
      deterministic rather than random, and the loser is read as a reused token — which revokes every
      live token for that user, including the one the winner just received. `ADR-0009` does not say
      whether that is intended. A short grace window on the just-rotated token would fix it without
      weakening rotation, but it is a behaviour change, so it needs a decision before the frontend
      starts holding sessions at `M2.4`. **`M2.4` has now shipped that session**, so the race is live
      rather than hypothetical: `lib/session.ts` serialises refreshes *within* a tab, and two tabs are
      two module instances sharing nothing. The decision now blocks a real behaviour, so it is worth
      settling before `M3` builds on the session.
- [ ] `QA-G5` The first `FOR UPDATE` probe reported `ModuleNotFoundError: No module named 'config'`
      because `uv run python /tmp/probe.py` puts the script's directory on `sys.path`, not the working
      directory. That was a fault in the harness, not the product, and it is recorded because a check
      that fails to run must never be reported as a pass.
- [ ] `QA-G6` The rate limits are per process, because the throttle store is the Django cache and it is
      set to `LocMemCache`. Two uvicorn workers would each allow the full rate, and a deploy clears the
      windows. That is correct for the single-process start command in `compose.yml` and in the Render
      config, and wrong the moment the service scales out — so a shared cache (Render Key Value, or the
      database cache if no extra service is wanted) is a prerequisite for a second worker, not a
      nice-to-have. Nothing in the code prevents the mistake, which is why it is written down here.
- [ ] `QA-G7` A weak password can be explained by the wrong reason. One rejected password returned two
      issues for the same field — "too similar to the email" before "too short" — and the form shows
      the first, so a three-character password is explained as similar rather than short. Both are
      true; only one tells the customer what to change. The order is Django's validator order, not
      ours, so the real choice is whether to show every issue for a field, to impose our own
      preference, or to accept whatever arrives first. Current behaviour is the last of those, and it
      is a microcopy question rather than a defect.
