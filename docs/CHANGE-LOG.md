# Plan Change Log

> **Append-only.** Never edit or delete an existing entry. New changes are added at the bottom.
> This log records changes to the **plan**, not to the code. Code changes are tracked by git history.

## Format

Each entry:

- **Version** — bumped from the previous (semver-ish: major = direction change, minor = scope change, patch = clarification).
- **Date**
- **Change** — what changed, stated as a delta from the previous plan.
- **Reason** — why (the forcing function).
- **Impact** — what it affects (scope, architecture, timeline, cost).
- **ADR** — link to the decision record, if any.

---

## v0.1.0 — 2026-10-04 — Baseline established

- **Change:** Initial baseline of the whole plan created.
- **Reason:** Project initiation. Planning precedes implementation by design.
- **Impact:** Established the project framing, MVP scope, architecture, and delivery approach.
- **Decisions baselined:**
  - Portfolio-as-simulated-business framing.
  - Domain: household goods; IKEA-inspired category and brand feel.
  - English UI; mock/sandbox payment first.
  - Decoupled monorepo: Django + Ninja backend, Next.js frontend, PostgreSQL.
  - JWT auth (access + refresh).
  - Free-tier deployment target: Render + Supabase + Vercel (+ Upstash later).
  - Documentation and change-control model (living `PLAN.md` + append-only `CHANGE-LOG.md` + ADRs).
  - Data-engineering track deferred to Phase 2.
- **ADRs:** `ADR-0001` … `ADR-0006`.

---

## v0.1.1 — 2026-10-04 — Brand name approved

- **Change:** The brand name was finalized as **NORDVIK** (previously a working title pending approval).
- **Reason:** Founder approval after review.
- **Impact:** Documentation no longer marked "working title"; the name becomes the storefront/UI brand. No change to scope, architecture, or timeline.
- **ADR:** `ADR-0007`.
