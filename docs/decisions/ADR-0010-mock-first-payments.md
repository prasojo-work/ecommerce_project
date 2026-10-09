# ADR-0010 — Mock-first payments

- **Status:** Accepted
- **Date:** 2026-10-09
- **Deciders:** Founder
- **Consulted hats:** senior_backend, senior_business_strategist, senior_cybersecurity

## Context

The store must demonstrate a complete checkout, but integrating a real payment provider
brings PCI scope, secret management, live keys, and compliance overhead that a portfolio
project does not need. The strategy (`STRATEGY.md`) already assumes a **simulated** payment.

## Options considered

1. **Real provider now (Stripe/Paddle).** Pros: real. Cons: PCI/compliance surface, live
   keys, cost, and a distraction from the engineering story.
2. **Mock-only, hard-coded.** Pros: trivial. Cons: no realistic seam; a real provider would
   require surgery later.
3. **Mock provider behind a `PaymentGateway` interface, selected by configuration.** Pros:
   demonstrates real integration design (ports and adapters) without the risk; failure paths
   are testable; a real provider becomes a drop-in adapter. Cons: none significant.

## Decision

Use **option 3**. A `PaymentGateway` interface has a **mock adapter** as the only v1
implementation, chosen by `PAYMENT_PROVIDER=mock`. The mock can simulate both **success** and
**failure** so the error path is testable (`API.md` §7). Real providers are integrated later
by adding an adapter, with no change to the Ordering module.

## Consequences

- No PCI scope; nothing to comply with; nothing to pay for.
- Checkout is fully exercised end to end, including the declined-payment path.
- The seam is explicit and documented, which reviewers read as good design.
- The mock endpoints are clearly namespaced and removed once a real provider exists.

## Reversibility

**Cheap.** Adding a real provider is a new adapter plus a config value; no domain change.

## References

- `docs/03-architecture/API.md` §7
- `docs/03-architecture/ARCHITECTURE.md` §6
