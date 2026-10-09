# TODO — System Architect (raw working file)

> Raw output of the `senior_system_architect` hat for LYSHEIM, committed for transparency.
> The curated, reviewer-facing versions are in [`../03-architecture/`](../03-architecture/).

## Context

- System: LYSHEIM — decoupled Next.js web app + Django 6 API over PostgreSQL, solo-built,
  free-tier hosted. Quality attributes prioritised: maintainability, security, finishability.

## System Design Items

- [x] **SYS-1.1 [Context & topology]** — decoupled two-app system; modular monolith API.
  Deliverable: `ARCHITECTURE.md` §2–§3.
- [x] **SYS-1.2 [Domain model / bounded contexts]** — Identity, Catalog, Cart, Ordering,
  Payments, Operations; Ordering stores product snapshots. Deliverable: `ARCHITECTURE.md` §4,
  `DATA-MODEL.md`.
- [x] **SYS-1.3 [Component design]** — Django apps + Next route groups. Deliverable:
  `ARCHITECTURE.md` §5.
- [x] **SYS-1.4 [Integration & data flow]** — synchronous REST; checkout sequence. Deliverable:
  `ARCHITECTURE.md` §6.
- [x] **SYS-1.5 [NFR architecture]** — performance, security, observability, money handling.
  Deliverable: `ARCHITECTURE.md` §7.
- [x] **SYS-1.6 [Deployment topology]** — dev/CI/prod. Deliverable: `ARCHITECTURE.md` §8,
  `ADR-0011`.
- [x] **SYS-1.7 [Phase 2 data platform outline]** — sources, ingestion, warehouse, serving.
  Deliverable: `ARCHITECTURE.md` §9.

## Decisions (ADRs)

- [x] `ADR-0005` API style & contract · `ADR-0006` Async & tasks · `ADR-0007` Operator console
  · `ADR-0008` Cart & guest merge · `ADR-0009` Auth & tokens · `ADR-0010` Mock payments ·
  `ADR-0011` Deployment · `ADR-0012` Image licensing.

## Risks / Unresolved

- [ ] `SYS-R1` Cross-site cookie + CORS correctness (Vercel↔Render). Mitigation: explicit
  tests in M2. Status: open.
- [ ] `SYS-R2` Supabase free connection limits under cold start. Mitigation: pooler + tuned
  `CONN_MAX_AGE`. Status: open.

## Commands

- N/A (design stage).
