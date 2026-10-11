"use client";

import { useState, type FormEvent } from "react";

import type { Address } from "@/api/account";
import { messageForFailure, type ApiFailure } from "@/lib/api-failure";
import {
  FIELDS,
  emptyValues,
  fieldErrors,
  validate,
  valuesFrom,
  type AddressField,
  type AddressValues,
} from "@/lib/address-form";

import { TextField } from "./text-field";

/**
 * How the form treats the default flag, decided by the caller because only it knows the situation:
 *
 * - `"checkbox"` — adding an address when the account already has one: a real choice.
 * - `"first"` — adding the first address, which the API makes the default whether or not anyone
 *   asks. A checkbox here would be a control that cannot do anything.
 * - `"none"` — editing, where the default is moved from the list instead. `API.md` section 8 refuses
 *   to let a default be cleared (`409`), so a checkbox that can only ever be re-ticked is a lie; the
 *   `PATCH` this form sends never carries `is_default` at all.
 */
export type DefaultControl = "checkbox" | "first" | "none";

/**
 * The address form (`US-2.5`), for both adding and editing.
 *
 * One form for both, because the error handling is the part that must exist once — the same reason
 * `AuthForm` serves sign-in and registration. What the caller answers is a validation failure or
 * nothing: on success this form does not even know what happened, the caller closes it.
 *
 * The caller keys this component by the address it is editing, so switching rows remounts the form
 * rather than leaving one address's text in another's inputs.
 */
export function AddressForm({
  initial,
  submitLabel,
  defaultControl,
  onSubmit,
  onCancel,
}: {
  /** The address being edited, or `null` to add one. */
  initial: Address | null;
  submitLabel: string;
  defaultControl: DefaultControl;
  /** Performs the request. A returned failure keeps the form open with the server's answer on it. */
  onSubmit: (values: AddressValues) => Promise<ApiFailure | null>;
  onCancel: () => void;
}) {
  const [values, setValues] = useState<AddressValues>(() =>
    initial === null ? emptyValues() : valuesFrom(initial),
  );
  const [errors, setErrors] = useState<Partial<Record<AddressField, string>>>({});
  const [failure, setFailure] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function update(field: AddressField, value: string): void {
    setValues((current) => ({ ...current, [field]: value }));
  }

  async function submit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();

    const local = validate(values);
    setErrors(local);
    setFailure(null);
    if (Object.keys(local).length > 0) {
      return;
    }

    setBusy(true);
    const reported = await onSubmit(values);
    setBusy(false);

    if (reported !== null) {
      setErrors(fieldErrors(reported.details));
      setFailure(messageForFailure(reported.status, reported.message));
    }
  }

  return (
    <form
      onSubmit={submit}
      noValidate
      className="mt-6 rounded-2xl border border-border bg-surface p-6"
    >
      {failure !== null && (
        <p
          role="alert"
          className="mb-5 rounded-lg border border-danger px-4 py-3 text-sm text-danger"
        >
          {failure}
        </p>
      )}

      <div className="grid gap-5 sm:grid-cols-2">
        {FIELDS.map((field) => (
          <div key={field.name} className={field.wide === true ? "sm:col-span-2" : undefined}>
            <TextField
              id={`address-${field.name}`}
              label={field.label}
              optional={!field.required}
              value={values[field.name]}
              error={errors[field.name]}
              autoComplete={field.autoComplete}
              type={field.name === "phone" ? "tel" : "text"}
              onChange={(value) => update(field.name, value)}
            />
          </div>
        ))}
      </div>

      {defaultControl === "checkbox" && (
        <label className="mt-5 flex min-h-11 items-center gap-3 text-sm">
          <input
            type="checkbox"
            checked={values.isDefault}
            onChange={(event) =>
              setValues((current) => ({ ...current, isDefault: event.target.checked }))
            }
            className="size-5"
          />
          Make this my default address
        </label>
      )}

      {defaultControl === "first" && (
        <p className="mt-5 text-sm text-muted">
          This will be your default address, because it is your first.
        </p>
      )}

      <div className="mt-6 flex flex-wrap items-center gap-4">
        <button
          type="submit"
          disabled={busy}
          className="min-h-11 rounded-lg bg-primary px-6 text-primary-ink disabled:opacity-60"
        >
          {busy ? "Saving…" : submitLabel}
        </button>
        <button
          type="button"
          onClick={onCancel}
          disabled={busy}
          className="min-h-11 text-primary underline disabled:opacity-60"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}
