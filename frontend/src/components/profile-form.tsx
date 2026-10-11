"use client";

import { useState, type FormEvent } from "react";

import { updateProfile } from "@/api/account";
import { fieldMessages, messageForFailure } from "@/lib/api-failure";
import type { SessionUser } from "@/lib/session";

import { TextField } from "./text-field";

/**
 * `PATCH /auth/me` (`US-2.4`) — the display name, and nothing else.
 *
 * The email is a line of prose rather than a disabled input: `ProfileUpdateSchema` carries one field,
 * so the address an account signs in with cannot be changed here, and a control that looks editable
 * but refuses every keystroke is worse than a sentence saying what is true. Changing it needs a
 * verification flow (a link to the new address, then confirmation) that does not exist yet, so it is
 * not offered rather than half-built.
 *
 * An empty name is allowed and saves: the API accepts it, and the header falls back to the email.
 * Blocking it here would refuse something the server would have taken.
 */
export function ProfileForm({ user }: { user: SessionUser }) {
  const [displayName, setDisplayName] = useState(user.display_name);
  const [error, setError] = useState<string | undefined>(undefined);
  const [failure, setFailure] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const [busy, setBusy] = useState(false);

  function update(value: string): void {
    setDisplayName(value);
    // The confirmation belongs to the value it confirmed, so editing retires it.
    setSaved(false);
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();

    setBusy(true);
    setFailure(null);
    const outcome = await updateProfile(displayName.trim());
    setBusy(false);

    if (outcome.ok) {
      setError(undefined);
      setSaved(true);
      return;
    }

    // The server is authoritative: a name it refused is reported against the input, and anything
    // else it says goes above the form rather than being lost.
    setError(fieldMessages(outcome.details).display_name);
    setFailure(messageForFailure(outcome.status, outcome.message));
  }

  return (
    <form onSubmit={onSubmit} noValidate className="mt-6 flex max-w-md flex-col gap-5">
      {failure !== null && (
        <p
          role="alert"
          className="rounded-lg border border-danger bg-surface px-4 py-3 text-sm text-danger"
        >
          {failure}
        </p>
      )}

      <TextField
        id="profile-display-name"
        label="Name"
        optional
        value={displayName}
        error={error}
        autoComplete="name"
        onChange={update}
      />

      <p className="text-sm text-muted">
        <span className="block">Email</span>
        <span className="block text-ink">{user.email}</span>
      </p>

      <div className="flex items-center gap-4">
        <button
          type="submit"
          disabled={busy}
          className="min-h-11 rounded-lg bg-primary px-6 text-primary-ink disabled:opacity-60"
        >
          {busy ? "Saving…" : "Save name"}
        </button>
        {/* A status region rather than an alert: nothing went wrong, and interrupting a screen
            reader mid-sentence to say so would be the wrong volume. */}
        <p role="status" className="text-sm text-success">
          {saved ? "Saved." : ""}
        </p>
      </div>
    </form>
  );
}
