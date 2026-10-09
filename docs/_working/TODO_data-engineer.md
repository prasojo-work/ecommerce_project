# TODO — Data Engineer (raw working file)

> Raw output of the `senior_data_engineer` hat for LYSHEIM. Phase 2 only
> (`SCOPE.md` `EPIC-7`). Curated source: [`../03-architecture/ARCHITECTURE.md`](../03-architecture/ARCHITECTURE.md) §9.

## Context

- The store is the *source system*. The data platform is built **after** v1 ships, so that
  the project mirrors how a real retailer grows a data capability.
- Consumers: the founder (portfolio) and a would-be stakeholder read (funnel, AOV, cohorts).

## Design Items (draft, Phase 2)

- [ ] **DE-1.1 [Source analysis]** — events (page view, product view, add-to-cart, checkout
  started, order placed) + transactional tables; volume is tiny (demo scale).
- [ ] **DE-1.2 [Ingestion]** — append-only `storefront_event` table and/or an Upstash queue
  drained by a worker (`ADR-0006` tasks).
- [ ] **DE-1.3 [Warehouse model]** — `analytics` schema, star-shaped: `fact_event`,
  `dim_product`, `dim_date`, `dim_customer` (surrogate keys).
- [ ] **DE-1.4 [Transformations]** — SQL models (dbt-style) for funnel, abandonment, AOV,
  cohorts; incremental where justified.
- [ ] **DE-1.5 [Data quality]** — not-null/uniqueness/referential checks; row-count anomalies.
- [ ] **DE-1.6 [Serving]** — a dashboard (metabase-style or a small Next view) over the marts.
- [ ] **DE-1.7 [Governance]** — PII minimisation (no raw emails in events), retention policy,
  lineage/definitions documented.

## Decisions

- [ ] `DE-ADR-1` choose warehouse (Supabase `analytics` schema vs Upstash) — at Phase 2 start.
- [ ] `DE-ADR-2` choose transformation tooling (dbt vs plain SQL + Make) — at Phase 2 start.

## Commands

- Planned: `python manage.py backfill_events`, `dbt run`, dashboard container — defined when
  Phase 2 begins.
