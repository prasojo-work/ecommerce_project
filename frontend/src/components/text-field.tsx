"use client";

/**
 * A labelled input with its error (`UX.md` section 7).
 *
 * Shared by the auth, profile and address forms, because the accessibility wiring is the part that
 * must not drift between them: `aria-invalid` plus `aria-describedby` is what turns the sentence
 * beside the input into something a screen reader announces as belonging to it, and `SCOPE.md`
 * NFR-2 forbids saying any of it with colour alone — the message is always text.
 *
 * Two attributes are deliberately absent:
 *
 * - **`required`**, because the browser's own bubble would be a second voice on the page saying
 *   something different from every other message on it. Each form runs its own check instead.
 * - **`maxLength`**, because it edits a paste in silence: a value past the model's bound is worth a
 *   sentence naming the bound, not a quiet truncation of what the customer typed.
 */
export function TextField({
  id,
  label,
  value,
  error,
  onChange,
  type = "text",
  autoComplete,
  optional = false,
}: {
  id: string;
  label: string;
  value: string;
  error: string | undefined;
  onChange: (value: string) => void;
  type?: "text" | "email" | "password" | "tel";
  autoComplete: string;
  optional?: boolean;
}) {
  const errorId = `${id}-error`;

  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="text-sm">
        {label}
        {optional && <span className="text-muted"> (optional)</span>}
      </label>
      <input
        id={id}
        name={id}
        type={type}
        value={value}
        autoComplete={autoComplete}
        aria-invalid={error !== undefined}
        aria-describedby={error === undefined ? undefined : errorId}
        onChange={(event) => onChange(event.target.value)}
        className="min-h-11 rounded-lg border border-border bg-surface px-3 aria-[invalid=true]:border-danger"
      />
      {error !== undefined && (
        <p id={errorId} className="text-sm text-danger">
          {error}
        </p>
      )}
    </div>
  );
}
