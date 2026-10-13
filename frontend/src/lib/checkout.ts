import type { components } from "@/api/schema";
import { cleanedAddress, type AddressValues } from "@/lib/address-form";

import type { Quote, ShippingOption } from "@/api/checkout";

/**
 * The checkout's own rules, kept out of the screen so they can be tested directly (`US-4.1`-`US-4.4`).
 *
 * Three things live here, and each is here for the same reason: it is a decision that is easy to get
 * subtly wrong and invisible when it is.
 *
 * 1. **Which step follows which.** `ADR-0006`'s spirit applied to a screen — the sequence is data, so
 *    the four steps cannot disagree about their own order.
 * 2. **What an address becomes on the wire.** The address book's form carries `label` and
 *    `isDefault`; a checkout sends neither (`QuoteAddressSchema`), and a payload built by hand in the
 *    component would be the place those two leaked in.
 * 3. **When an order still needs settling.** The single most consequential branch in this flow, and
 *    the one a retry walks into: see `needsSettlement`.
 */

export type CheckoutAddress = components["schemas"]["QuoteAddressSchema"];

export type Step = "address" | "shipping" | "payment" | "done";

/**
 * The four steps, in order. `done` is the confirmation, which is why it is a step rather than a
 * fifth page: the order number belongs to the same journey as the button that produced it.
 */
export const STEPS: readonly Step[] = ["address", "shipping", "payment", "done"];

/** The one-based number of a step, for "Step 2 of 4". `done` is not one of the four. */
export function stepNumber(step: Step): number {
  return STEPS.indexOf(step) + 1;
}

/** How many steps the customer is asked to fill in. The confirmation is not one of them. */
export const STEP_COUNT = STEPS.length - 1;

/** Every step but the last has somewhere to go. */
export function nextStep(step: Step): Step | null {
  const next = STEPS[STEPS.indexOf(step) + 1];
  return next ?? null;
}

/** The first step has nowhere to go back to. */
export function previousStep(step: Step): Step | null {
  const index = STEPS.indexOf(step);
  return index <= 0 ? null : (STEPS[index - 1] ?? null);
}

/**
 * The address as `QuoteAddressSchema` wants it, from the form's own values.
 *
 * The trimming and the country's upper-casing come from `lib/address-form.ts` rather than being
 * repeated, because those are the rules the address book already enforces and a checkout that
 * spelled a country differently would be storing a second version of it.
 */
export function addressPayload(values: AddressValues): CheckoutAddress {
  const address = cleanedAddress(values);

  // `label` is dropped deliberately, and explicitly rather than by spreading and deleting: a checkout
  // does not name an address or make one the default, so the two fields are absent by decision.
  return {
    recipient: address.recipient,
    line1: address.line1,
    line2: address.line2,
    city: address.city,
    region: address.region,
    postal_code: address.postal_code,
    country: address.country,
    phone: address.phone,
  };
}

/** The fields every address-shaped payload here shares, so a saved and a new one can be read alike. */
export type PostalAddress = {
  recipient: string;
  line1: string;
  line2: string;
  city: string;
  region: string;
  postal_code: string;
  country: string;
};

/**
 * The address as a single line, recipient first and blank parts dropped.
 *
 * Deliberately not `addressLines` from `lib/address-form.ts`, which answers a different question: that
 * one lines up an address-*book card*, where a label has taken the heading and the recipient is
 * therefore repeated underneath it. A checkout has no label and is not a card — it is a destination,
 * so the recipient leads and nothing is repeated.
 *
 * Blank parts are dropped rather than left as gaps: `line2` and `region` are optional, and an address
 * with a hole in the middle of it reads as a mistake.
 */
export function postalLine(address: PostalAddress): string {
  return [
    address.recipient,
    address.line1,
    address.line2,
    address.city,
    address.region,
    address.postal_code,
    address.country,
  ]
    .filter((part) => part !== "")
    .join(", ");
}

/** The shipping option a code names, or `undefined` if the quote does not offer it. */
export function optionFor(quote: Quote, code: string): ShippingOption | undefined {
  return quote.shipping_options.find((option) => option.code === code);
}

/** The first option, which is what a quote preselects. */
export function defaultMethodCode(quote: Quote): string {
  return quote.shipping_options[0]?.code ?? "";
}

/**
 * Does this order still have a payment to settle?
 *
 * **This is the branch a retry depends on.** Placing an order and settling it are two calls, so the
 * first can succeed while the second's response is lost — the customer sees a failure, clicks again,
 * and `Idempotency-Key` answers with the *same* order. Settling it a second time is a `409` ("nothing
 * left to settle"), which would report a failure for an order that is already paid for.
 *
 * So the order's own status decides. Only `pending` has a payment waiting on it; anything else has
 * already been decided, by this checkout or by one that ran before.
 */
export function needsSettlement(order: { status: string }): boolean {
  return order.status === "pending";
}

/**
 * One key per checkout attempt (`NFR-4`).
 *
 * `crypto.randomUUID` is available in every browser this app supports and, unlike a counter or a
 * timestamp, cannot collide across two tabs checking out at once — which is the case that would
 * otherwise charge one customer twice.
 */
export function newIdempotencyKey(): string {
  return crypto.randomUUID();
}
