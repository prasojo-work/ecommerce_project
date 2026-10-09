# TODO — Cloud Engineer (raw working file)

> Raw output of the `senior_cloud_engineer` hat for LYSHEIM. Curated source:
> [`../03-architecture/ARCHITECTURE.md`](../03-architecture/ARCHITECTURE.md) §8 and
> [`../decisions/ADR-0011-deployment-stack.md`](../decisions/ADR-0011-deployment-stack.md).

## Context

- Goal: a publicly reachable demo at zero cost (`GOAL-1`, `NFR-8`).
- Targets: Vercel (web), Render (API + worker), Supabase (Postgres), Upstash (Phase 2).
- Constraint: solo operator; minimise manual ops; keep the platform portable.

## Design Items

- [ ] **CLOUD-1.1 [Topology]** — web (Vercel) → API (Render container) → Postgres (Supabase);
  health probe on `/healthz`.
- [ ] **CLOUD-1.2 [Containerisation]** — `backend/Dockerfile`; reproducible image; non-root.
- [ ] **CLOUD-1.3 [Configuration]** — one set of env vars, documented in `.env.example`;
  per-platform dashboards; no secrets in git.
- [ ] **CLOUD-1.4 [Cold-start mitigation]** — periodic keep-alive ping; document the
  expectation for reviewers.
- [ ] **CLOUD-1.5 [Database]** — Supabase pooler (PgBouncer); tuned `CONN_MAX_AGE`; documented
  backup/restore (`pg_dump`).
- [ ] **CLOUD-1.6 [Observability]** — platform logs + JSON app logs; uptime check on `/healthz`.
- [ ] **CLOUD-1.7 [Cost guardrails]** — stay within free tiers; no paid add-ons.
- [ ] **CLOUD-1.8 [Runbook]** — deploy steps, rollback, and "seed the demo" recorded in
  `docs/04-delivery/RUNBOOK.md`.

## IaC note

- [ ] **CLOUD-1.9** Full IaC (Terraform/Pulumi) is **out of scope for v1**; the platform
  dashboards plus a documented runbook are sufficient at this scale. Revisit if environments
  multiply.

## Commands

- Build: `docker build -t lysheim-api backend/` · Smoke: `curl -fsS $API_URL/healthz`
