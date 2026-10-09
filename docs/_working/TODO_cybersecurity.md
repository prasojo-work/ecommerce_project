# TODO — Cybersecurity (raw working file)

> Raw output of the `senior_cybersecurity` hat for LYSHEIM, committed for transparency. The
> curated, reviewer-facing version is
> [`../06-quality/SECURITY-BASELINE.md`](../06-quality/SECURITY-BASELINE.md).

## Context

- System: LYSHEIM — Next.js web app, Django 6 API, PostgreSQL, Django admin, mock payment,
  mocked email.
- Data classification: public (catalog), internal (ops), confidential (PII: email/name/
  address), secret (password hashes, JWT key, DB creds, refresh tokens). No regulated data
  (payments are mock).
- Compliance: PCI-DSS n/a; GDPR-relevant handling (minimisation, retention, erasure).
- Scope: application + identity + secrets + transport + logging + privacy. Out of scope: MFA,
  WAF, pen-testing, exploit development (by policy).

## Threat Model and Findings

- [ ] **SEC-FIND-1.1 [AuthN]**: token exposure via JS-readable storage.
  Risk: High×High. Component: web session. Remediation: in-memory access + httpOnly refresh.
- [ ] **SEC-FIND-1.2 [AuthZ]**: IDOR on orders/addresses/cart. Risk: Medium×High. Component:
  API. Remediation: server-side ownership checks + tests.
- [ ] **SEC-FIND-1.3 [Injection]**: raw SQL / string-built queries. Risk: Medium×High.
  Component: backend. Remediation: ORM only + Ninja schema validation.
- [ ] **SEC-FIND-1.4 [XSS]**: unescaped rendering. Risk: Medium×High. Component: frontend.
  Remediation: React escaping; CSP; no `dangerouslySetInnerHTML`.
- [ ] **SEC-FIND-1.5 [Secrets]**: credentials in code/logs/git. Risk: Low×Critical. Component:
  all. Remediation: env-only; git-ignore; secret guard; no PII in logs.
- [ ] **SEC-FIND-1.6 [DoS]**: unthrottled auth/order endpoints. Risk: Medium×Medium.
  Remediation: throttling; bounded pagination; body-size limits.
- [ ] **SEC-FIND-1.7 [Admin]**: operator console exposure. Risk: Medium×High. Remediation:
  strong password, `is_staff`, throttled login, not linked publicly. MFA accepted residual.
- [ ] **SEC-FIND-1.8 [Supply chain]**: vulnerable/unpinned deps. Risk: Medium×High.
  Remediation: lockfiles + audits in CI.
- [ ] **SEC-FIND-1.9 [Logging]**: PII/secrets in logs. Risk: Medium×Medium. Remediation:
  field allow-list + redaction.
- [ ] **SEC-FIND-1.10 [Transport]**: missing HSTS/Secure/CORS. Remediation: HTTPS, HSTS,
  cookie flags, CORS allow-list.
- [ ] **SEC-FIND-1.11 [CSRF]**: cookie auth CSRF. Remediation: origin check + SameSite, scoped
  path.
- [ ] **SEC-FIND-1.12 [Cart]**: forged cart cookie. Risk: Low×Low. Remediation: signed cookie;
  totals rebuilt server-side.

## Remediation Plan

- [ ] `SEC-REMEDIATE-1.1`..`1.12` — one per finding; priorities and validations in
  `SECURITY-BASELINE.md` §5. Critical: `1.5`. High: `1.1,1.2,1.3,1.4,1.7`.

## Proposed Configuration/Code Changes

- Headers, cookie attributes, and CORS policy are specified in `SECURITY-BASELINE.md` §6.

## Commands

- `uv run pip-audit` · `uv run python manage.py check --deploy` · `pnpm audit --prod` ·
  `curl -sI https://<api-host>/healthz`.

## Quality checklist

- [x] Threat model covers all components/boundaries · [x] Findings risk-prioritised ·
- [x] No exploit code included · [x] Compliance mapped · [x] Detection accompanies prevention.
