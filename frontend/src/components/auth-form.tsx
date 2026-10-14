"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { login, register } from "@/api/auth";
import { fieldMessages, messageForFailure } from "@/lib/api-failure";
import { validate, type AuthMode, type AuthValues } from "@/lib/auth-form";

import { TextField } from "./text-field";

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
      // The account screen, because a signed-in visitor's next move is usually to check or edit
      // something — and because the header's account entry now leads somewhere.
      router.push("/account");
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
        <TextField
          id="display-name"
          label="Name"
          optional
          value={values.displayName}
          error={errors.displayName}
          autoComplete="name"
          onChange={(value) => update("displayName", value)}
        />
      )}

      <TextField
        id="email"
        label="Email"
        type="email"
        value={values.email}
        error={errors.email}
        autoComplete="email"
        onChange={(value) => update("email", value)}
      />

      <TextField
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

      {/* Underlined on purpose. Tailwind's preflight gives an anchor the colour *and* the decoration
          of the text around it, so without this the link is set apart by colour alone — the one
          thing WCAG 1.4.1 forbids. The `M6.2` route audit is what found it. */}
      <p className="text-sm text-muted">
        {registering ? (
          <>
            Already have an account?{" "}
            <Link href="/login" className="text-primary underline underline-offset-4">
              Sign in
            </Link>
          </>
        ) : (
          <>
            New here?{" "}
            <Link href="/register" className="text-primary underline underline-offset-4">
              Create an account
            </Link>
          </>
        )}
      </p>
    </form>
  );
}
