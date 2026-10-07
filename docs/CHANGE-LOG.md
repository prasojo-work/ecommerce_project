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

---

## v0.1.2 — 2026-10-07 — Delivery approach changed (assistant-authored increments)

- **Change:** The delivery approach changed from "teaching mode" (the founder transcribes every file the assistant proposes) to **assistant-authored, founder-reviewed** increments: the assistant writes the code directly, keeps it passing all quality gates, adds unit tests, and commits each increment; the founder reviews and directs.
- **Reason:** Chat-rendered code containing `${...}` template literals and literal angle-bracket markup was mangled on paste (surfacing as `MATH1` / `HTML11`), corrupting files and failing builds. The founder also elected to review working increments rather than transcribe them.
- **Impact:** No change to scope, architecture, timeline, or cost. Changes *how* work is produced and verified; each increment now ends in a green gate and a commit.
- **ADR:** `ADR-0009`.

---

## v0.1.3 — 2026-10-07 — M4 clarifications: shipping selection and order numbering

- **Change:** Two clarifications to the data model, decided while building M4 (checkout & orders):
  - `order` gains `shipping_method` and `shipping_method_name`. Shipping options are defined in code, not in a table; standard delivery is free at or above Rp 500.000.
  - The `order.number` format is fixed as `NDV-<YYYY>-<zero-padded pk>` (e.g. `NDV-2026-000123`).
- **Reason:** `DATA-MODEL.md` enumerates `order` with only a `shipping_cost` column, yet `ARCHITECTURE.md` §4 assigns "shipping" to the `orders` app and `UX.md` requires shipping *options with cost and ETA* before payment. Separately, `DATA-MODEL.md` describes `order.number` only as a "human ref, unique" and fixes no format.
- **Impact:** Two additive `order` columns and one generated field format. No change to scope, endpoints, or cost.
- **ADR:** `ADR-0010`.

---

## v0.1.4 — 2026-10-07 — Documentation reconciled with the code

- **Change:** An audit of every story and every table against the implementation, run before starting M6:
  - `SCOPE.md`: the story checkboxes now reflect reality across M1–M5, and **`US-5.3`'s acceptance criterion was corrected**. It promised a payment record "with status `paid`", but `paid` is an *order* status (`DATA-4.1`) while the payment status is `succeeded` (`DATA-5.1`). The code was already correct; the story was wrong.
  - `DATA-MODEL.md`: the catalog, cart, accounts, orders and payments tables are all now marked built, and two design claims that were never implemented are corrected — the unenforced money check constraints on the catalog and cart columns, and the missing `product_variant(product_id, is_active)` index.
- **Reason:** The task brief makes these documents the source of truth and forbids undocumented drift. The checkboxes had gone stale at every milestone boundary since M1, and `US-5.3` directly contradicted `DATA-5.1`.
- **Impact:** Documentation only — no code, schema or scope change. Two previously invisible gaps are now recorded in the roadmap's *Known gaps*: `US-2.2` is missing its price-range filter, availability filter and "popularity" sort, and `US-3.3` is missing profile editing. Neither is delivered nor descoped yet; that is a decision for the founder.
- **ADR:** None — this makes the documents match the code rather than changing a decision.

