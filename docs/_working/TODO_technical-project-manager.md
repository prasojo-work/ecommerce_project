# TODO — Technical Project Manager (raw working file)

> Raw output of the `senior_technical_project_manager` hat for LYSHEIM, committed for
> transparency per the working agreement. The curated, reviewer-facing version is
> [`../02-product/SCOPE.md`](../02-product/SCOPE.md).

## Context

- Project: **LYSHEIM** v1 — storefront + operator console.
- Objectives: a deployed, seeded, end-to-end demo that proves commercial thinking and senior
  engineering (see `PLAN.md` §2 goals `GOAL-1..6`).
- Timeline/budget: solo; no fixed calendar; budget is an available model API key.
- Stakeholders: the founder (sponsor, product owner, reviewer) and the "reviewer" audience
  (recruiter / freelance client).
- Success criteria: the five evidence gates in `PLAN.md` §2.

## Project Plan (workstreams)

- [ ] **PLAN-1 [Foundations — M0]**: repo, CI, Docker Compose, both apps boot, seeding, env
  segregation. Owner: Founder. Deps: none. Exit: `docker compose up` runs both apps.
- [ ] **PLAN-2 [Catalog & browse — M1]**: catalog models, API, listing/PDP UI, search,
  filter/sort, curated images. Owner: Founder. Deps: PLAN-1.
- [ ] **PLAN-3 [Accounts & auth — M2]**: register/login, JWT access+refresh, profile,
  addresses. Owner: Founder. Deps: PLAN-1.
- [ ] **PLAN-4 [Cart — M3]**: server-side cart, guest merge, quantity/stock rules. Deps: PLAN-2, PLAN-3.
- [ ] **PLAN-5 [Checkout & orders — M4]**: address, shipping, mock payment, orders +
  confirmation (Tasks framework). Deps: PLAN-4.
- [ ] **PLAN-6 [Operator console — M5]**: catalog/stock/order management. Deps: PLAN-2, PLAN-5.
- [ ] **PLAN-7 [Hardening — M6]**: tests, a11y, performance, security, credits page. Deps: all.
- [ ] **PLAN-8 [Deploy — M7]**: Render + Vercel + Supabase, runbook, keep-alive. Deps: PLAN-7.
- [ ] **PLAN-9 [Data track — M8, Phase 2]**: events → warehouse → dashboard. Deps: PLAN-8.

## Risk Register

- [ ] **RISK-1 [Scope creep]** — Probability: High / Impact: High. Owner: Founder.
  Mitigation: hard MVP boundary (`SCOPE.md` §5), change control (ADR + changelog). Status: open.
- [ ] **RISK-2 [Free-tier cold starts]** — Prob: Medium / Impact: Medium. Mitigation:
  keep-alive ping; document in the deploy ADR. Status: open.
- [ ] **RISK-3 [Portfolio thinness]** — Prob: Medium / Impact: High. Mitigation: real domain
  model, tests, live demo, docs. Status: open.
- [ ] **RISK-4 [Infinite re-planning / stalls]** — Prob: Medium / Impact: High. Mitigation:
  small vertical slices; fixed v1 finish line. Status: open.
- [ ] **RISK-5 [Image licensing]** — Prob: Medium / Impact: Medium. Mitigation: credits page
  (`US-6.1`), policy ADR. Status: open.
- [ ] **RISK-6 [Async complexity]** — Prob: Low / Impact: Medium. Mitigation: use async only
  where it pays off (`PLAN.md` §5); keep a sync fallback. Status: open.

## Communication Plan

- The founder is the sole stakeholder. Reporting happens in-session after each increment
  ("what changed, how to run it"). Durable record lives in `CHANGE-LOG.md` and the commits.

## Commands / Artifacts

- Tracking artifacts: this repo's `docs/` (plan, scope, roadmap, ADRs). No external tracker.
