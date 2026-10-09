# LYSHEIM — Project Documentation

> **Brand:** `LYSHEIM` — approved 2026-10-09 (see [`decisions/ADR-0003-brand-name.md`](decisions/ADR-0003-brand-name.md)).

LYSHEIM is a **home-goods e-commerce store** — a portfolio project that models a real,
IKEA-inspired retail business and then builds a production-grade slice of it. It exists to
demonstrate, to a recruiter or a freelance client, both **commercial thinking** and **senior
engineering execution**.

## What this documentation is for

Two audiences, one artifact set:

- **The reviewer** (recruiter or client) — reads these docs to judge how the project was
  *thought about*, not only what was coded.
- **The builder** (the author, wearing every hat) — uses these docs as the working memory of
  the project, so decisions are never silently relitigated.

## Documentation map

```
docs/
├── README.md                 ← you are here (index + conventions)
├── PLAN.md                   ← the LIVING master plan (always current)
├── CHANGE-LOG.md             ← APPEND-ONLY record of plan changes
├── WORKING-AGREEMENT.md      ← how the work is executed increment by increment
├── 01-business/
│   └── STRATEGY.md           ← market, model, positioning, unit economics
├── 02-product/               ← scope, personas, epics, UX (Stage 2)
├── 03-architecture/          ← C4 views, modules, API, data model, deployment (Stage 3)
├── 04-delivery/              ← roadmap, risk register, RACI, runbook (Stage 4)
├── 05-qa/
│   ├── scenarios/            ← test scenarios written by the builder
│   └── results/              ← results written by the tester agent (immutable to the builder)
├── _working/                 ← raw agent TODO files, committed for transparency
│   └── TODO_business-strategist.md
└── decisions/
    ├── ADR-0000-template.md
    ├── ADR-0001-monorepo-structure.md
    ├── ADR-0002-documentation-and-change-control.md
    ├── ADR-0003-brand-name.md
    └── ADR-0004-working-agreement.md
```

## Conventions

- **Stable IDs.** Every trackable item carries a prefix: `GOAL-`, `EPIC-`, `US-` (user
  story), `NFR-`, `SYS-`, `DATA-`, `PLAN-`, `RISK-`, `STRAT-`, `ADR-`. IDs are never reused
  or renumbered; retired items are marked `[DROPPED]` and kept for history.
- **Checkboxes.** Actionable items are written as GitHub checkboxes so progress is visible
  in the repo and parseable by tools.
- **Living vs append-only.** `PLAN.md` is *living* — edited in place to reflect current
  truth. `CHANGE-LOG.md` and the ADRs are *append-only* — history is never rewritten.
- **ADRs.** One file per significant decision, numbered sequentially, never edited after
  acceptance (only `status` changes, e.g. `Accepted → Superseded by ADR-NNNN`).
- **Solo framing.** This is a solo project. The roles in `the_team/` are used as *thinking
  hats*, not as a fake org chart.
- **Language.** The storefront, code, and docs are English-first; the market is
  international and prices are in USD.

## Reading order

For a first read: `PLAN.md` → `01-business/STRATEGY.md` → `02-product/SCOPE.md` →
`03-architecture/ARCHITECTURE.md` → `04-delivery/ROADMAP.md`.

## How the plan changes

This project deliberately simulates a start-up in which the plan moves. When the plan
changes:

1. The decision is captured as an **ADR**.
2. The delta and its rationale are appended to **`CHANGE-LOG.md`**.
3. **`PLAN.md`** is re-baselined to the new truth and its version is bumped.

So the plan is always current, and the *history of change* stays inspectable. See
`ADR-0002`.
