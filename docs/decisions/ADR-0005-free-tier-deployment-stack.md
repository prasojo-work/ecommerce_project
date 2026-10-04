# ADR-0005: Free-tier deployment stack (Render + Supabase + Vercel)

- **Status:** Accepted
- **Date:** 2026-10-04
- **Deciders:** Founder
- **Related:** `ADR-0001`, `ADR-0004`

## Context

The project must have a **live, publicly reachable demo** (a portfolio without a URL is just code). The author wants **free** hosting, while the architecture must not be locked to any one provider. Local development uses Docker Compose; production must be reachable by a recruiter with a single click.

## Options considered

1. **Render (API) + Supabase (Postgres) + Vercel (frontend)** — all free, all managed, minimal ops, git-push deploys. Cost: free tiers **sleep/pause** when idle.
2. **Fly.io (API+DB) + Vercel** — more container-native, but tighter free allowances and a database to operate.
3. **A single VPS** — full control, but the author becomes a sysadmin, and it is not free.
4. **AWS free tier** — most "enterprise-credible", but the free tier is time-limited and the setup burden is large for a portfolio.

## Decision

Use the **free managed stack**: **Vercel** (Next.js frontend), **Render** (Django API), **Supabase** (PostgreSQL), with **Upstash** Redis reserved for the Phase 2 data track. Everything is configured via environment variables so the target is swappable.

## Consequences

- **Positive:** zero cost; minimal ops; instant git-push deploys; Postgres requirement satisfied by Supabase.
- **Negative / costs:** Render's free web service **sleeps after ~15 min idle** (~30–60 s cold start); Supabase free projects **pause after ~7 days idle**; Supabase free tier has tight connection limits (use the pooler). These trade-offs are real and are mitigated, not hidden.
- **Follow-ups:** add a keep-alive ping (free cron / GitHub Actions) to stay warm; document the deploy runbook; write the provider-swap steps into the docs so the hosting choice remains reversible.

## Reversibility

**Medium–High.** Because the app is containerized and fully configured by env vars, moving to another host is a configuration change plus a deploy, not a rewrite.
