"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { listAddresses, type Address } from "@/api/account";
import { loadCart } from "@/api/cart";
import {
  fetchQuote,
  placeOrder,
  settlePayment,
  type Order,
  type Quote,
  type SettlementAttempt,
} from "@/api/checkout";
import { addressLines, headingFor } from "@/lib/address-form";
import { messageForFailure } from "@/lib/api-failure";
import { linesOf } from "@/lib/cart";
import {
  addressPayload,
  defaultMethodCode,
  needsSettlement,
  newIdempotencyKey,
  nextStep,
  optionFor,
  postalLine,
  previousStep,
  STEP_COUNT,
  stepNumber,
  STEPS,
  type CheckoutAddress,
  type Step,
} from "@/lib/checkout";
import { formatPrice } from "@/lib/money";

import { AddressForm } from "./address-form";
import { useCart } from "./cart-provider";
import { EmptyState } from "./empty-state";
import { useSession } from "./session-provider";

/**
 * `/checkout` (`US-4.1`-`US-4.4`) — the client half, because the whole flow is behind a token that
 * only exists in memory (`ADR-0009`), so none of it can be rendered on the server.
 *
 * The four steps are held in one component rather than spread across four routes, and that is a
 * decision about what a checkout *is*: a half-finished order is not a page anyone can be linked to or
 * reload into, so there is nothing for a URL to mean. One component also means the address a customer
 * chose and the method they picked are still in scope when the payment is taken, instead of being
 * passed through a query string the customer could edit.
 *
 * **The three states before the steps** mirror `/cart`, and for the same reasons: the token may still
 * be coming back from the refresh cookie, the cart is a signed-in feature (`ADR-0017`), and an empty
 * cart has nothing to check out. A checkout that skipped the second would offer a flow that could
 * only fail at the end.
 */
export function CheckoutScreen() {
  const { status } = useSession();
  const { cart, failure } = useCart();

  const [step, setStep] = useState<Step>("address");
  const [addresses, setAddresses] = useState<Address[] | null>(null);
  const [addressesFailure, setAddressesFailure] = useState<string | null>(null);
  const [choice, setChoice] = useState<Choice | null>(null);
  const [enteringNew, setEnteringNew] = useState(false);
  const [quote, setQuote] = useState<Quote | null>(null);
  const [method, setMethod] = useState("");
  const [order, setOrder] = useState<Order | null>(null);
  const [problem, setProblem] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  /**
   * One key for the whole checkout rather than one per click.
   *
   * It is a ref because it must survive re-renders: a key regenerated while the customer watched
   * would be a new key for the same attempt, which is the one thing an idempotency key may not do.
   *
   * It is also `null` until an attempt actually starts, rather than made here. A key generated during
   * render would be made while the page is being prerendered and baked into the shell, which `next
   * build` refuses outright — `crypto.randomUUID()` in a Client Component is an unstable value — and
   * which would be wrong anyway: the key belongs to the moment the customer asks to pay.
   */
  const idempotencyKey = useRef<string | null>(null);

  function keyForThisAttempt(): string {
    const existing = idempotencyKey.current;
    if (existing !== null) {
      return existing;
    }

    const created = newIdempotencyKey();
    idempotencyKey.current = created;
    return created;
  }

  useEffect(() => {
    if (status !== "authenticated") {
      return;
    }

    let active = true;
    void (async () => {
      const outcome = await listAddresses();
      if (!active) {
        return;
      }

      if (outcome.ok) {
        setAddresses(outcome.addresses);
        return;
      }

      // An empty list rather than `null` on failure, so the step stops loading and offers the way in
      // that always works: typing the address. The failure is shown beside it.
      setAddresses([]);
      setAddressesFailure(messageForFailure(outcome.status, outcome.message));
    })();

    return () => {
      active = false;
    };
  }, [status]);

  /** The two ways to give an address (`US-4.1`), as the two payload shapes the API accepts. */
  function requestFor(selected: Choice) {
    return selected.kind === "saved"
      ? { address_id: selected.address.id }
      : { address: selected.address };
  }

  /**
   * Take the address and ask for the quote (`US-4.1`, `US-4.2`).
   *
   * The quote is fetched here rather than when the order is placed because reading it is the first
   * thing that can refuse an address — and a refusal belongs beside the address, not at the end of a
   * checkout the customer has already filled in.
   */
  async function continueWith(selected: Choice): Promise<void> {
    setProblem(null);
    setChoice(selected);
    setBusy(true);

    const outcome = await fetchQuote(requestFor(selected));

    setBusy(false);

    if (!outcome.ok) {
      setProblem(messageForFailure(outcome.status, outcome.message));
      return;
    }

    setQuote(outcome.quote);
    setMethod(defaultMethodCode(outcome.quote));
    setStep("shipping");
  }

  /**
   * Place the order and settle it (`US-4.3`).
   *
   * Two calls, and the order between them is the API's: `POST /orders` reserves the stock and
   * `POST /payments/mock/...` decides whether the order keeps it. Both are needed whichever way the
   * payment goes — a decline is a real outcome of a real order, which is why it cancels one rather
   * than never creating it.
   */
  async function settle(attempt: SettlementAttempt): Promise<void> {
    if (choice === null) {
      return;
    }

    setProblem(null);
    setBusy(true);

    const placed = await placeOrder(
      { ...requestFor(choice), shipping_method: method },
      keyForThisAttempt(),
    );

    if (!placed.ok) {
      setBusy(false);
      setProblem(messageForFailure(placed.status, placed.message));
      return;
    }

    setOrder(placed.order);

    /**
     * A replay can answer with an order that is already decided.
     *
     * The two calls below are separate, so the first can land while the second's response is lost —
     * the customer sees a failure, presses again, and the key returns the *same* order. Settling it
     * twice is a `409`, which would report a failure for an order that is already paid for. So what
     * is left to do is read from the order, not assumed from the attempt.
     */
    if (!needsSettlement(placed.order)) {
      setBusy(false);
      void loadCart();
      go(nextStep("payment"));
      return;
    }

    const settled = await settlePayment(placed.order.number, attempt);

    setBusy(false);

    if (!settled.ok) {
      // The order exists and is still `pending`, so pressing either button again is the right way
      // out; the key makes that safe.
      setProblem(messageForFailure(settled.status, settled.message));
      return;
    }

    setOrder({ ...placed.order, status: settled.settlement.order_status });

    // The cart became the order, so the header's count is stale until it is read again. Deliberately
    // not awaited: the confirmation is not a place to wait on a badge.
    void loadCart();
    go(nextStep("payment"));
  }

  /**
   * Move between steps.
   *
   * The sequence itself lives in `lib/checkout.ts`, so no button here knows what follows it — and
   * the failure shown above is cleared, because it belonged to the step being left.
   */
  function go(target: Step | null): void {
    if (target === null) {
      return;
    }

    setProblem(null);
    setStep(target);
  }

  if (status === "restoring") {
    return <p className="mt-10 text-muted">Loading…</p>;
  }

  if (status !== "authenticated") {
    return (
      <div className="mt-10 rounded-2xl border border-dashed border-border bg-surface px-8 py-16 text-center">
        <h2 className="text-xl">Sign in to check out</h2>
        <p className="mx-auto mt-3 max-w-measure text-muted">
          Your cart and your delivery addresses belong to your account.
        </p>
        <p className="mt-6">
          <Link
            href="/login"
            className="inline-flex min-h-11 items-center rounded-lg bg-primary px-6 text-primary-ink"
          >
            Sign in
          </Link>
        </p>
      </div>
    );
  }

  if (cart === null) {
    if (failure !== null) {
      return (
        <div
          role="alert"
          className="mt-10 rounded-2xl border border-border bg-surface px-8 py-12 text-center"
        >
          <p className="mx-auto max-w-measure text-muted">{failure}</p>
          <button
            type="button"
            onClick={() => void loadCart()}
            className="mt-6 inline-flex min-h-11 items-center rounded-lg border border-border px-6"
          >
            Try again
          </button>
        </div>
      );
    }

    return <p className="mt-10 text-muted">Loading…</p>;
  }

  if (linesOf(cart).length === 0 && step !== "done") {
    return (
      <EmptyState
        title="There is nothing to check out"
        description="Your cart is empty, so there is nothing to deliver yet."
        action={
          <Link
            href="/products"
            className="inline-flex min-h-11 items-center rounded-lg bg-primary px-6 text-primary-ink"
          >
            Browse the catalog
          </Link>
        }
      />
    );
  }

  return (
    <div className="mt-8">
      <ol className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm">
        {STEPS.slice(0, STEP_COUNT).map((candidate) => (
          <li
            key={candidate}
            aria-current={step === candidate ? "step" : undefined}
            className={step === candidate ? "font-medium" : "text-muted"}
          >
            {stepNumber(candidate)}. {STEP_LABELS[candidate]}
          </li>
        ))}
      </ol>

      {problem !== null && (
        <p
          role="alert"
          className="mt-6 rounded-lg border border-danger bg-surface px-4 py-3 text-sm text-danger"
        >
          {problem}
        </p>
      )}

      {step === "address" && (
        <section aria-labelledby="delivery-heading" className="mt-8">
          <h2 id="delivery-heading" className="text-xl">
            Where should it go?
          </h2>
          <p className="mt-2 max-w-measure text-muted">
            Choose a saved address, or enter a new one. This is what we ship to, and it is saved
            with the order as it is today.
          </p>

          {addressesFailure !== null && (
            <p role="alert" className="mt-6 text-sm text-danger">
              {addressesFailure} You can still enter an address below.
            </p>
          )}

          {addresses === null && <p className="mt-6 text-muted">Loading your addresses…</p>}

          {addresses !== null && addresses.length > 0 && (
            <ul className="mt-6 flex flex-col gap-3">
              {addresses.map((address) => (
                <li key={address.id}>
                  <button
                    type="button"
                    onClick={() => void continueWith({ kind: "saved", address })}
                    disabled={busy}
                    className="w-full rounded-2xl border border-border bg-surface p-4 text-left disabled:opacity-60"
                  >
                    <span className="font-medium">{headingFor(address)}</span>
                    <span className="mt-1 block text-sm text-muted">
                      {addressLines(address).join(", ")}
                    </span>
                    <span className="mt-2 inline-block text-sm text-primary">
                      {busy ? "Working…" : "Deliver here"}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}

          {enteringNew ? (
            // The address book's own form, which is the point of it being one component: the fields,
            // the local checks and the API's field errors are the ones `US-2.5` already earned. It
            // answers a second failure by *not* returning one — this screen shows the message above,
            // where the step is, rather than pinning a checkout refusal to a field it did not come
            // from.
            <AddressForm
              initial={null}
              submitLabel="Deliver here"
              defaultControl="none"
              onCancel={() => setEnteringNew(false)}
              onSubmit={async (values) => {
                await continueWith({ kind: "new", address: addressPayload(values) });
                return null;
              }}
            />
          ) : (
            <button
              type="button"
              onClick={() => setEnteringNew(true)}
              className="mt-4 min-h-11 text-primary underline"
            >
              Use a new address
            </button>
          )}
        </section>
      )}

      {step === "shipping" && quote !== null && (
        <section aria-labelledby="shipping-heading" className="mt-8">
          <h2 id="shipping-heading" className="text-xl">
            How should it travel?
          </h2>
          <p className="mt-2 max-w-measure text-muted">
            {quote.item_count === 1 ? "1 item" : `${String(quote.item_count)} items`}, subtotal{" "}
            {formatPrice(quote.subtotal)}.
          </p>

          <fieldset className="mt-6">
            <legend className="text-sm text-muted">Shipping method</legend>
            <ul className="mt-3 flex flex-col gap-3">
              {quote.shipping_options.map((option) => (
                <li key={option.code}>
                  <label className="flex cursor-pointer items-start gap-3 rounded-2xl border border-border bg-surface p-4">
                    <input
                      type="radio"
                      name="shipping-method"
                      value={option.code}
                      checked={method === option.code}
                      onChange={() => setMethod(option.code)}
                      className="mt-1 size-5"
                    />
                    <span className="flex-1">
                      <span className="font-medium">{option.name}</span>
                      <span className="mt-1 block text-sm text-muted">{option.description}</span>
                    </span>
                    <span className="text-sm">{formatPrice(option.price)}</span>
                  </label>
                </li>
              ))}
            </ul>
          </fieldset>

          <div className="mt-6 flex flex-wrap items-center gap-4">
            <button
              type="button"
              onClick={() => go(nextStep("shipping"))}
              disabled={method === ""}
              className="min-h-11 rounded-lg bg-primary px-6 text-primary-ink disabled:opacity-60"
            >
              Continue to payment
            </button>
            <button
              type="button"
              onClick={() => go(previousStep("shipping"))}
              className="min-h-11 text-primary underline"
            >
              Back
            </button>
          </div>
        </section>
      )}

      {step === "payment" && quote !== null && (
        <section aria-labelledby="payment-heading" className="mt-8">
          <h2 id="payment-heading" className="text-xl">
            Pay
          </h2>
          <p className="mt-2 max-w-measure text-muted">
            LYSHEIM is a demonstration store, so the payment is simulated: no card is asked for and
            no money moves (`ADR-0010`). Either outcome is a real one to try.
          </p>

          <Summary
            rows={[
              { label: "Subtotal", value: formatPrice(quote.subtotal) },
              {
                label: optionFor(quote, method)?.name ?? "Shipping",
                value: formatPrice(optionFor(quote, method)?.price ?? quote.subtotal),
              },
            ]}
            total={formatPrice(optionFor(quote, method)?.total ?? quote.subtotal)}
          />

          {/* `UX.md` flow C asks for a review before the confirm, and where it is going is half of
              what is being reviewed — the other half is the total above. */}
          {choice !== null && (
            <p className="mt-4 text-sm text-muted">Delivering to {postalLine(choice.address)}</p>
          )}

          <div className="mt-6 flex flex-wrap items-center gap-4">
            <button
              type="button"
              onClick={() => void settle("capture")}
              disabled={busy}
              className="min-h-11 rounded-lg bg-primary px-6 text-primary-ink disabled:opacity-60"
            >
              {busy ? "Working…" : "Pay now"}
            </button>
            {/* `US-4.3` asks for failure to be reachable rather than hoped for, which is why the
                decline is a control and not a coincidence. */}
            <button
              type="button"
              onClick={() => void settle("decline")}
              disabled={busy}
              className="min-h-11 rounded-lg border border-border px-6 disabled:opacity-60"
            >
              Simulate a declined payment
            </button>
            <button
              type="button"
              onClick={() => go(previousStep("payment"))}
              disabled={busy}
              className="min-h-11 text-primary underline disabled:opacity-60"
            >
              Back
            </button>
          </div>
        </section>
      )}

      {step === "done" && order !== null && (
        <section aria-labelledby="confirmation-heading" className="mt-8">
          <h2 id="confirmation-heading" className="text-xl">
            {order.status === "paid"
              ? "Thank you — your order is placed"
              : "Your payment did not go through"}
          </h2>

          <p className="mt-2 max-w-measure text-muted">
            {order.status === "paid"
              ? `Order ${order.number}. We have emailed a confirmation, and it will be signed for at the address below.`
              : `Order ${order.number} was cancelled and its stock returned, so nothing will be sent and nothing was charged.`}
          </p>

          <p className="mt-4 text-sm">
            <span className="text-muted">Status</span>{" "}
            <span className="font-medium">{order.status}</span>
          </p>

          <Summary
            rows={[
              { label: "Subtotal", value: formatPrice(order.subtotal) },
              { label: "Shipping", value: formatPrice(order.shipping) },
            ]}
            total={formatPrice(order.total)}
          />

          <h3 className="mt-8 text-lg">What you ordered</h3>
          <ul className="mt-3 flex flex-col gap-2 text-sm">
            {order.items.map((item) => (
              <li
                key={`${item.product_name}-${item.variant_name}`}
                className="flex justify-between gap-4"
              >
                <span>
                  {item.quantity} × {item.product_name} ({item.variant_name})
                </span>
                <span>{formatPrice(item.line_total)}</span>
              </li>
            ))}
          </ul>

          <h3 className="mt-8 text-lg">Delivering to</h3>
          <p className="mt-3 text-sm text-muted">{postalLine(order.shipping_address)}</p>

          <p className="mt-8">
            <Link href="/products" className="min-h-11 text-primary underline">
              Back to the catalog
            </Link>
          </p>
        </section>
      )}
    </div>
  );
}

/** What the address step decided. `null` until it has decided anything. */
type Choice = { kind: "saved"; address: Address } | { kind: "new"; address: CheckoutAddress };

const STEP_LABELS: Record<Step, string> = {
  address: "Delivery",
  shipping: "Shipping",
  payment: "Payment",
  done: "Confirmation",
};

/**
 * A two-row total and one emphasised line, for the payment and confirmation steps.
 *
 * The total is passed in rather than added up here: on the payment step it is the shipping option's
 * own `total`, which is the API's arithmetic for the method currently chosen, and on the confirmation
 * it is the order's. A component that summed its rows would be a third implementation of `API.md`
 * section 1.
 */
function Summary({ rows, total }: { rows: { label: string; value: string }[]; total: string }) {
  return (
    <dl className="mt-6 max-w-sm rounded-2xl border border-border bg-surface p-6 text-sm">
      {rows.map((row) => (
        <div key={row.label} className="flex justify-between gap-4">
          <dt className="text-muted">{row.label}</dt>
          <dd>{row.value}</dd>
        </div>
      ))}
      <div className="mt-3 flex justify-between gap-4 border-t border-border pt-3 text-base">
        <dt>Total</dt>
        <dd className="font-medium">{total}</dd>
      </div>
    </dl>
  );
}
