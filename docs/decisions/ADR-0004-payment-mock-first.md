# ADR-0004: Mock payment first, real gateway later

- **Status:** Accepted
- **Date:** 2026-10-04
- **Deciders:** Founder
- **Related:** `ADR-0005`

## Context

Checkout needs a payment step. A real gateway (Stripe for international, Midtrans/Xendit for Indonesia) requires KYC, business credentials, and merchant onboarding — none of which are sensible for a portfolio demo, and some of which may not be available to the author at all. Yet checkout must *feel* real to a reviewer, and the payment boundary must be designed so a real provider can slot in later.

## Options considered

1. **Real gateway now (Stripe/Midtrans)** — most realistic, but blocked on onboarding/credentials and adds external failure modes to the demo.
2. **Mock/sandbox payment** — a simulated payment that creates a real `payment` record and transitions the order to `paid`. Zero onboarding, fully demoable, and the interface mirrors a real provider.
3. **No payment step** — checkout "just works". Cheapest, but the domain would be less honest and less impressive.

## Decision

Implement a **mock payment provider behind a defined interface** (`payments` context with a `provider` field). The mock creates a `payment` record and marks the order paid. The interface is designed so a real provider is an additive change.

## Consequences

- **Positive:** fully demoable with no credentials; the payment boundary is explicit and future-proof; the UI can honestly label it "demo — no real charge".
- **Negative / costs:** not a real transaction; must be clearly labelled to avoid misleading anyone; a future provider integration still requires its own ADR and work.
- **Follow-ups:** when a real gateway is added, record it as a new ADR superseding part of this one; keep the mock available for local development/tests.

## Reversibility

**High.** Because the provider sits behind an interface, adding a real gateway is additive rather than a rewrite.
