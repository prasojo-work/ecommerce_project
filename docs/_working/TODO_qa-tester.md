# TODO — QA (`qa_tester`)

**Scope:** the authentication surface as it stands after `M2.2` — `accounts.User`, `accounts.Address`,
`accounts.RefreshToken`, and the five endpoints `POST /auth/register`, `POST /auth/login`,
`POST /auth/refresh`, `POST /auth/logout`, `GET /auth/me` (`SCOPE.md` `US-2.1`–`US-2.3`, `ADR-0009`,
`API.md` section 2).

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

**Levels.** 30 API contract tests (`backend/tests/test_accounts_api.py`), 20 model tests
(`test_accounts_models.py`), and a scripted end-to-end pass over real HTTP, because cookie attributes
and headers cannot be verified through the test client alone. The suite and the flow were run twice:
once on SQLite, then again on PostgreSQL 17.11, because the two differ in exactly the place that
matters here (see `QA-C30`).

**Deliberately not tested.** JWT signing internals and password hashing internals (libraries' jobs, not
ours), TLS and transport hardening (`M7`).

**Blocked, not skipped.** Rate limiting and the `/auth/refresh` origin guard are `M2.3`; browser-level
CORS and cross-site cookie behaviour are `M2.4`. Nothing else is blocked — the suite and the whole flow
have now been run on PostgreSQL as well as SQLite.

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

### Not run

- [ ] `QA-C26` **Not run — blocked to `M2.3`.** Rate limiting: that `N` failed logins within a window
      produce `429` with `Retry-After`. No throttle exists yet, so there is nothing to test.
- [ ] `QA-C27` **Not run — blocked to `M2.3`.** `/auth/refresh` from a foreign `Origin` is refused.
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
- [ ] `QA-C31` **Not run — `M2.6`.** Address ownership: user A must not be able to read, edit or delete
      user B's address. No address endpoint exists yet, but the rule belongs in the test plan before it
      does — this is the classic broken-object-level-authorization failure.
- [ ] `QA-C32` **Not run — `M2.6`.** `PATCH /auth/me` for the display name is specified by `US-2.4` but
      absent from `API.md`; the contract needs the endpoint before it can be tested.

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

## QA-GAP — questions for the product owner

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
      starts holding sessions at `M2.4`.
- [ ] `QA-G5` The first `FOR UPDATE` probe reported `ModuleNotFoundError: No module named 'config'`
      because `uv run python /tmp/probe.py` puts the script's directory on `sys.path`, not the working
      directory. That was a fault in the harness, not the product, and it is recorded because a check
      that fails to run must never be reported as a pass.
