# Risk Register — LYSHEIM

> Consulted hats: **Senior Technical Project Manager** and **Senior Technical Lead**. Owner:
> Founder. Reviewed at each milestone gate. Expands `PLAN.md` §9.

| ID | Risk | Category | Prob. | Impact | Mitigation | Status |
|---|---|---|---|---|---|---|
| `RISK-1` | **Scope creep** — e-commerce can absorb unlimited features. | Delivery | High | High | Hard MVP boundary (`SCOPE.md` §5); change control via ADR + change log; Phase 2 gated behind v1. | Open |
| `RISK-2` | **Free-tier cold starts** — first request after idle is slow. | Ops | High | Medium | Keep-alive ping; documented expectation for reviewers (`ADR-0011`). | Open |
| `RISK-3` | **Portfolio thinness** — a "toy" store impresses no one. | Outcome | Medium | High | Real domain model, tests, deployed demo, written strategy, and the Phase 2 data track. | Open |
| `RISK-4` | **Infinite re-planning / stalled momentum** — the number-one way portfolio projects die. | Delivery | Medium | High | Thin vertical slices; every increment demoable; fixed v1 finish line. | Open |
| `RISK-5` | **Image licensing / unsuitable imagery** — some images are CC BY-ND or semantically wrong. | Legal | Medium | Medium | Attribution page (`US-6.1`); curation in M1; policy in `ADR-0012`. | Open |
| `RISK-6` | **Async complexity** — mixing sync and async incorrectly. | Technical | Low | Medium | Async only where it pays (`ADR-0006`); sync fallback; conventions documented in M0. | Open |
| `RISK-7` | **Cross-site cookie / CORS bugs** — Vercel↔Render refresh flow fails in production. | Technical | Medium | Medium | Explicit tests in M2; origin/CSRF guard; production smoke test in M7. | Open |
| `RISK-8` | **Free-tier limits** — Supabase connections, Render spin-down, build minutes. | Ops | Medium | Medium | Connection pooler + tuned `CONN_MAX_AGE`; path-filtered CI; monitored in M7. | Open |
| `RISK-9` | **Key-person / continuity** — a solo author with gaps in the history. | Delivery | Low | Medium | Everything (docs, decisions, runbook) lives in the repo, not in the author's head. | Open |

**Review cadence.** Reviewed at every milestone gate. Probability and impact are re-scored,
and any risk that has materialised becomes an entry in [`../CHANGE-LOG.md`](../CHANGE-LOG.md)
with the response taken.
