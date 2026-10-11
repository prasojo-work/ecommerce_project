"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { login, register } from "@/api/auth";
import {
  fieldMessages,
  messageForFailure,
  validate,
  type AuthMode,
  type AuthValues,
} from "@/lib/auth-form";

/**
 * One form for both endpoints (`US-2.1`, `US-2.2`, `UX.md` flow D).
 *
 * Two components would have duplicated the error handling, which is the part worth having in exactly
 * one place: the field errors the API reports, the form-level message, the busy state, and the rule
 * that the server's answer always wins over the client's pre-check.
 *
 * `noValidate` is deliberate even though the inputs carry `type="email"`. The browser's own bubble
 * would otherwise appear first and say something different from every other message on this form;
 * taking the form over means one voice. Validation itself lives in `lib/auth-form.ts`, where it is
 * tested, and the API remains authoritative — on a rejected submit its `details` are what is shown.
 */
export function AuthForm({ mode }: { mode: AuthMode }) {
  const router = useRouter();
  const [values, setValues] = useState<AuthValues>({ email: "", password: "", displayName: "" });
  const [errors, setErrors] = useState<Partial<Record<keyof AuthValues, string>>>({});
  const [failure, setFailure] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const registering = mode === "register";

  function update(field: keyof AuthValues, value: string): void {
    setValues((current) => ({ ...current, [field]: value }));
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();

    const local = validate(mode, values);
    setErrors(local);
    setFailure(null);
    if (Object.keys(local).length > 0) {
      return;
    }

    setBusy(true);
    const outcome = registering
      ? await register(values.email.trim(), values.password, values.displayName.trim())
      : await login(values.email.trim(), values.password);
    setBusy(false);

    if (outcome.ok) {
      // Home for now, because `/account` arrives with `M2.6`. The header is the confirmation: it
      // reads the session store, so it switches to the account as soon as this resolves.
      router.push("/");
      return;
    }

    // The API is authoritative, so anything it reports replaces what we guessed. `display_name` is
    // the server's name for the input this form calls `displayName`.
    const reported = fieldMessages(outcome.details);
    setErrors({
      email: reported.email,
      password: reported.password,
      displayName: reported.display_name,
    });
    setFailure(messageForFailure(outcome.status, outcome.message));
  }

  return (
    <form onSubmit={onSubmit} noValidate className="mt-8 flex flex-col gap-5">
      {failure !== null && (
        <p
          role="alert"
          className="rounded-lg border border-danger bg-surface px-4 py-3 text-sm text-danger"
        >
          {failure}
        </p>
      )}

      {registering && (
        <Field
          id="display-name"
          label="Name"
          optional
          value={values.displayName}
          error={errors.displayName}
          autoComplete="name"
          onChange={(value) => update("displayName", value)}
        />
      )}

      <Field
        id="email"
        label="Email"
        type="email"
        value={values.email}
        error={errors.email}
        autoComplete="email"
        onChange={(value) => update("email", value)}
      />

      <Field
        id="password"
        label="Password"
        type="password"
        value={values.password}
        error={errors.password}
        autoComplete={registering ? "new-password" : "current-password"}
        onChange={(value) => update("password", value)}
      />

      <button
        type="submit"
        disabled={busy}
        className="min-h-11 rounded-lg bg-primary px-6 text-primary-ink disabled:opacity-60"
      >
        {busy ? "Please wait…" : registering ? "Create account" : "Sign in"}
      </button>

      <p className="text-sm text-muted">
        {registering ? (
          <>
            Already have an account? <Link href="/login">Sign in</Link>
          </>
        ) : (
          <>
            New here? <Link href="/register">Create an account</Link>
          </>
        )}
      </p>
    </form>
  );
}

/**
 * A labelled input with its error.
 *
 * `aria-invalid` plus `aria-describedby` is what turns the message beside the input into something a
 * screen reader announces as belonging to it. The error is also a sentence in the flow, never a
 * colour: `SCOPE.md` NFR-2 forbids encoding state by colour alone.
 *
 * There is no `required` attribute, because the browser's own message would be a second voice; the
 * error text below is the only one.
 */
function Field({
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
  type?: "text" | "email" | "password";
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
