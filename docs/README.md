# NORDVIK — Project Documentation

> **Brand:** `NORDVIK` — approved 2026-10-04 (see [`decisions/ADR-0007-brand-name.md`](decisions/ADR-0007-brand-name.md)).

NORDVIK is a **home-goods e-commerce store** — a portfolio project that models a real IKEA-inspired retail business and then builds a production-grade slice of it. It exists to demonstrate, to a recruiter or freelance client, both **commercial thinking** and **senior engineering execution**.

## What this documentation is for

Two audiences, one artifact set:

- **The reviewer** (recruiter/client) — reads these docs to judge how the project was *thought about*, not just what was coded.
- **The builder** (the author, wearing every hat) — uses these docs as the working memory of the project so decisions are never silently relitigated.

## Documentation map

```
docs/
├── README.md                 ← you are here (index + conventions)
├── PLAN.md                   ← the LIVING master plan (always current)
├── CHANGE-LOG.md             ← APPEND-ONLY record of plan changes
├── 01-business/
│   └── STRATEGY.md           ← market, model, positioning, unit economics
├── 02-product/
│   ├── SCOPE.md              ← personas, epics, user stories, in/out of scope, NFRs
│   └── UX.md                 ← IA, key flows, design language, accessibility
├── 03-architecture/
│   ├── ARCHITECTURE.md       ← C4 views, modules, API, deployment, NFRs
│   └── DATA-MODEL.md         ← entities, relationships, constraints
├── 04-delivery/
│   └── ROADMAP.md            ← milestones, workstreams, risks, RACI, change control
└── decisions/
    ├── ADR-0000-template.md
    ├── ADR-0001-monorepo-structure.md
    ├── ADR-0002-api-layer-django-ninja.md
    ├── ADR-0003-authentication-jwt.md
    ├── ADR-0004-payment-mock-first.md
    ├── ADR-0005-free-tier-deployment-stack.md
    └── ADR-0006-documentation-and-change-control.md
```

## Conventions

- **Stable IDs.** Every trackable item carries a prefix: `EPIC-`, `US-` (user story), `NFR-`, `SYS-`, `DATA-`, `PLAN-`, `RISK-`, `ADR-`, `STRAT-`. IDs are never reused or renumbered; retired items are marked `[DROPPED]` and kept for history.
- **Checkboxes.** Actionable items are written as GitHub checkboxes so progress is visible in the repo and parseable by tools.
- **Living vs append-only.** `PLAN.md` is *living* — it is edited in place to reflect the current truth. `CHANGE-LOG.md` and the ADRs are *append-only* — history is never rewritten.
- **ADRs.** One file per significant decision, numbered sequentially, never edited after acceptance (only `status` changes, e.g. `Accepted → Superseded by ADR-XXXX`).
- **Solo framing.** This is a solo project. Roles from `the_team/` are used as *thinking hats*, not as a fake org chart.

## Reading order

For a first read: `PLAN.md` → `01-business/STRATEGY.md` → `02-product/SCOPE.md` → `03-architecture/ARCHITECTURE.md` → `04-delivery/ROADMAP.md`.

## How the plan changes

This project deliberately simulates a start-up where the plan moves. When the plan changes:

1. A decision is captured as an **ADR**.
2. The delta and its rationale are appended to **`CHANGE-LOG.md`**.
3. **`PLAN.md`** is re-baselined to the new truth.

So the plan is always current, and the *history of change* remains inspectable. See `ADR-0006`.
