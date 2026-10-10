/**
 * The add-to-cart action `US-1.2` asks for, as the placeholder `M1.6` calls for.
 *
 * Nothing is specified about what a placeholder should do, and the real behaviour belongs to
 * `US-3.1` at `M3` (feedback, header count, stock capping). So it is a genuinely disabled control
 * with the reason stated in visible text and wired up with `aria-describedby` — a disabled button
 * that does not say why reads as broken, and a button that pretends to work would be worse.
 *
 * A Server Component: there is no behaviour to attach yet, so this costs no client JavaScript.
 */
export function AddToCartButton() {
  return (
    <div className="flex flex-col items-start gap-2">
      <button
        type="button"
        disabled
        aria-describedby="add-to-cart-note"
        className="inline-flex min-h-11 items-center rounded-lg bg-primary px-6 text-primary-ink disabled:opacity-60"
      >
        Add to cart
      </button>
      <p id="add-to-cart-note" className="text-sm text-muted">
        Ordering isn&apos;t open yet.
      </p>
    </div>
  );
}
