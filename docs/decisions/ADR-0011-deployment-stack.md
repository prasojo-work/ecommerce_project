# ADR-0011 — Deployment stack and free-tier constraints

- **Status:** Accepted
- **Date:** 2026-10-09
- **Deciders:** Founder
- **Consulted hats:** senior_cloud_engineer, senior_backend, senior_frontend_engineering

## Context

The project must be **publicly reachable at no cost** (`GOAL-1`, `NFR-8`). The founder chose
free-tier targets: **Render** (backend), **Vercel** (frontend), **Supabase** (Postgres), and
**Upstash** for the Phase 2 data work. Free tiers impose real constraints, and the deployment
must be reproducible and portable so it is not hostage to one vendor.

## Options considered

1. **Render + Vercel + Supabase + Upstash.** Pros: generous free tiers, managed Postgres,
   git-push deploys, container and serverless options. Cons: cold starts on Render's free
   web service; Supabase free connection limits.
2. **A single vendor.** Pros: one dashboard. Cons: free tiers are more restrictive per
   service, and it reduces the demonstrated multi-service integration.
3. **Self-hosted VPS.** Pros: full control. Cons: cost, ops burden, and no free tier.

## Decision

Adopt **option 1**. Additional decisions:

- The backend runs as a **container** (Dockerfile) so it is portable across hosts.
- A **health endpoint** (`/healthz`) is the uptime probe.
- **Cold starts** on Render's free web service are accepted and mitigated with a periodic
  keep-alive ping plus a documented expectation on the README/reviewer instructions.
- Database access uses the **Supabase connection pooler** (PgBouncer) to stay within free
  connection limits, with `CONN_MAX_AGE` tuned accordingly.
- Every environment difference is a **variable** (`ARCHITECTURE.md` §8), so moving hosts
  changes configuration only.

## Consequences

- Zero running cost, at the price of occasional latency on the first request after idle.
- Two dashboards to manage secrets; `.env.example` documents the single set of keys.
- Portable image + config keeps the exit cost from any one vendor low.

## Reversibility

**Moderate.** The containerized backend and env-based config make a host migration routine;
the managed Postgres is the least portable piece but a standard `pg_dump`/restore covers it.

## References

- `docs/PLAN.md` §4
- `docs/03-architecture/ARCHITECTURE.md` §8
