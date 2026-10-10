import { RetryButton } from "./retry-button";

/**
 * The catalog error state: `UX.md` section 5 asks for a retry panel, and section 9 asks that the
 * copy name the problem and the fix. The heading names the situation, `message` names the cause,
 * and the button is the fix.
 */
export function RetryPanel({ message }: { message: string }) {
  return (
    <div
      role="alert"
      className="mt-8 rounded-2xl border border-border bg-surface px-8 py-16 text-center"
    >
      <h2 className="text-xl">The catalog is unavailable</h2>
      <p className="mx-auto mt-3 max-w-measure text-muted">{message}</p>
      <RetryButton />
    </div>
  );
}
