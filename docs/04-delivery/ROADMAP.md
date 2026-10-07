# Delivery Roadmap — NORDVIK

> Consulted hats: **Technical Project Manager** (lead), **Technical Lead**. Owner: Founder.
> Heavyweight PM ceremony is unnecessary for a team of one — what *is* necessary is a clear sequence, an honest risk register, and a defined way to handle change.

---

## Context

- **Objective:** ship a live, polished, documented home-goods store as a portfolio artifact, in thin vertical slices that are always demoable.
- **Team:** solo. Roles below are *hats*, not people.
- **Cadence:** work proceeds in weekly-ish increments; each milestone ends with a working demo and a doc update.
- **Success criteria:** the goals in [`PLAN.md`](../PLAN.md#2-goals--success-criteria) are met and the store is publicly reachable.

## Milestones

Each milestone ends only when its **exit criteria** are met and its slice is committed and green in CI.

- [x] **PLAN-1.1 [M0 — Foundations]** — *complete (2026-10-05)*
  - **Deliverable:** monorepo skeleton; both apps boot locally via Docker Compose; CI runs lint/type-check/tests.
  - **Exit criteria:** `docker compose up` serves the API `/health` and a Next.js page; CI is green.
  - **Depends on:** —
- [x] **PLAN-1.2 [M1 — Catalog & browse]** — *complete (2026-10-07)*
  - **Deliverable:** categories, products, variants, images; list + detail + search/filter/sort (`EPIC-1`, `EPIC-2`).
  - **Exit criteria:** a shopper can browse and find a product; pagination works; catalog reads are cached.
  - **Depends on:** M0.
- [x] **PLAN-1.3 [M2 — Accounts & auth]** — *complete (2026-10-07)*
  - **Deliverable:** register/login/refresh, profile, addresses (`EPIC-3`).
  - **Exit criteria:** JWT flow works end to end; protected endpoints reject anonymous requests.
  - **Depends on:** M0.
- [ ] **PLAN-1.4 [M3 — Cart]**
  - **Deliverable:** server-side cart for logged-in users (`EPIC-4`).
  - **Exit criteria:** cart persists across sessions/devices; quantity math correct.
  - **Depends on:** M1, M2.
- [ ] **PLAN-1.5 [M4 — Checkout & orders]**
  - **Deliverable:** address → shipping → mock payment → order + history (`EPIC-5`, `EPIC-6`).
  - **Exit criteria:** a full purchase completes; stock decremented under lock; order is an immutable snapshot; duplicate submit is idempotent.
  - **Depends on:** M3.
- [ ] **PLAN-1.6 [M5 — Admin]**
  - **Deliverable:** manage products/variants/inventory/orders (`EPIC-7`).
  - **Exit criteria:** catalog and order status are manageable without touching the DB.
  - **Depends on:** M1, M4.
- [ ] **PLAN-1.7 [M6 — Hardening]**
  - **Deliverable:** NFR pass — tests, accessibility, performance, security review.
  - **Exit criteria:** coverage on domain logic + critical flows; axe clean; Lighthouse ≥ 90 on key pages; OWASP review documented.
  - **Depends on:** M4, M5.
- [ ] **PLAN-1.8 [M7 — Deploy]**
  - **Deliverable:** live demo on Render + Supabase + Vercel; keep-alive ping; deploy docs.
  - **Exit criteria:** public URL works; cold-start mitigated; secrets in host env only.
  - **Depends on:** M6.
- [ ] **PLAN-1.9 [M8 — Data-engineering track (Phase 2)]**
  - **Deliverable:** event capture → warehouse → dashboard.
  - **Exit criteria:** defined in a *future* plan revision (deliberately not detailed yet).
  - **Depends on:** M7, and on the plan being re-baselined to include it.

## Definition of Done (every slice)

A slice is done only when **all** hold:
- [ ] Acceptance criteria for its user stories pass.
- [ ] Unit/integration tests cover the domain logic it introduces.
- [ ] Lint + type checks are clean (`ruff`, `basedpyright`, ESLint, `tsc`).
- [ ] It is demoable from a clean `docker compose up`.
- [ ] Docs updated (and a change-log entry added if the *plan* moved).

## Risk register

- [ ] **RISK-1 [Scope creep]**
  - **Probability/Impact:** High / High — e-commerce invites endless features.
  - **Owner:** Founder (PM hat). **Mitigation:** hard MVP boundary in [`SCOPE.md`](../02-product/SCOPE.md); every addition goes through change control. **Status:** open.
- [ ] **RISK-2 [Free-tier cold starts]**
  - **Probability/Impact:** High / Medium — Render and Supabase sleep when idle.
  - **Owner:** Founder (Cloud hat). **Mitigation:** keep-alive ping; warm the demo before sharing; documented in `ADR-0005`. **Status:** open.
- [ ] **RISK-3 [Portfolio perceived as a toy]**
  - **Probability/Impact:** Medium / High — a shallow store impresses no one.
  - **Owner:** Founder. **Mitigation:** real domain model, tests, deployed demo, credible strategy doc. **Status:** open.
- [ ] **RISK-4 [Momentum loss / burnout]**
  - **Probability/Impact:** Medium / High — solo projects stall.
  - **Owner:** Founder. **Mitigation:** thin vertical slices, always demoable; milestone-based progress. **Status:** open.
- [ ] **RISK-5 [Auth/security mistakes]**
  - **Probability/Impact:** Medium / High — a portfolio with an obvious hole backfires.
  - **Owner:** Founder (Security hat). **Mitigation:** M6 security review; OWASP checklist. **Status:** open.
- [ ] **RISK-6 [Technical debt from going fast]**
  - **Probability/Impact:** Medium / Medium. **Owner:** Founder (Tech Lead hat). **Mitigation:** DoD above; refactor slices tracked in the backlog. **Status:** open.

## RACI (hats, one person)

| Activity | Responsible | Accountable | Consulted | Informed |
|---|---|---|---|---|
| Strategy & scope | Business/PM hats | Founder | — | — |
| Architecture & data | Architect/Backend hats | Founder | Security | — |
| Backend build | Backend hat | Founder | Architect | — |
| Frontend build | Frontend/UI-UX hats | Founder | Backend | — |
| Quality & review | Code-reviewer/QA hats | Founder | Architect | — |
| Deploy & operate | Cloud hat | Founder | Security | — |
| Plan change decisions | PM hat | Founder | relevant hat | — |

## Change control

Because this project deliberately simulates a start-up where the plan moves, change is expected — but never silent:

1. **Raise** the proposed change (a note in the relevant doc or the chat).
2. **Decide** — record it as an **ADR** with context, options, decision, consequences.
3. **Log** the delta + rationale in [`CHANGE-LOG.md`](../CHANGE-LOG.md).
4. **Re-baseline** [`PLAN.md`](../PLAN.md) and bump its version.
5. **Re-plan** affected milestones/workstreams here.

Change is always *welcomed*; what is not allowed is undocumented drift.

## Reporting

- **To self (working memory):** `PLAN.md` + `CHANGE-LOG.md` are the source of truth.
- **To reviewers:** the repo itself — a clean commit history, green CI, and these docs.
- **Cadence:** update `CHANGE-LOG.md` whenever the plan moves; re-baseline `PLAN.md` at each milestone boundary.

## Quality checklist

- [x] Scope, objectives, and success criteria are explicit.
- [x] Every milestone has an owner, dependency, and exit criteria.
- [x] Risk register covers the top risks with mitigation and owners.
- [x] Change-control process is documented.
- [x] Reporting cadence defined.
