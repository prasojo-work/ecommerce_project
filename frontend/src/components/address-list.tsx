"use client";

import { useCallback, useEffect, useState } from "react";

import {
  createAddress,
  deleteAddress,
  listAddresses,
  updateAddress,
  type Address,
} from "@/api/account";
import { messageForFailure, type ApiFailure } from "@/lib/api-failure";
import {
  addressLines,
  headingFor,
  toCreatePayload,
  toUpdatePayload,
  type AddressValues,
} from "@/lib/address-form";

import { AddressForm, type DefaultControl } from "./address-form";
import { EmptyState } from "./empty-state";

/**
 * The address book (`US-2.5`) — the whole section, because it is the only thing that knows what the
 * addresses are.
 *
 * It owns the list rather than rendering one it was handed, because every action here changes what
 * the list should be, and a parent holding that state would only be passing it back down. The form
 * stays presentational: it reports a validation failure and the list decides what to do with it.
 */

type Editing = { mode: "closed" } | { mode: "adding" } | { mode: "editing"; address: Address };

export function AddressList() {
  const [addresses, setAddresses] = useState<Address[] | null>(null);
  const [loadFailure, setLoadFailure] = useState<string | null>(null);
  const [actionFailure, setActionFailure] = useState<string | null>(null);
  const [editing, setEditing] = useState<Editing>({ mode: "closed" });
  const [pendingId, setPendingId] = useState<number | null>(null);
  const [confirmingId, setConfirmingId] = useState<number | null>(null);

  const load = useCallback(async (): Promise<void> => {
    const outcome = await listAddresses();

    if (outcome.ok) {
      setAddresses(outcome.addresses);
      setLoadFailure(null);
      return;
    }

    // A `401` here is not a list problem: the session store has already been emptied by the failed
    // renewal, so `AccountScreen` renders the signed-out state and unmounts this. Anything else is
    // a load failure worth showing.
    setLoadFailure(messageForFailure(outcome.status, outcome.message));
  }, []);

  useEffect(() => {
    // Wrapped in the async IIFE rather than called directly, which is the shape `session-provider`
    // uses: the state this sets lands after the await, so it is not a synchronous set during the
    // effect body — the thing `react-hooks/set-state-in-effect` exists to prevent.
    void (async () => {
      await load();
    })();
  }, [load]);

  async function makeDefault(address: Address): Promise<void> {
    setPendingId(address.id);
    setActionFailure(null);
    const outcome = await updateAddress(address.id, { is_default: true });
    setPendingId(null);

    if (!outcome.ok) {
      setActionFailure(messageForFailure(outcome.status, outcome.message));
      return;
    }

    // Rearranged from the response rather than re-read: `API.md` section 8 returns the promoted row,
    // the rest can only have lost the flag, and the default goes first — which is the order the
    // endpoint itself promises, so this reproduces it rather than inventing one.
    setAddresses((current) => {
      if (current === null) {
        return current;
      }
      const others = current.filter((row) => row.id !== address.id);
      return [outcome.address, ...others.map((row) => ({ ...row, is_default: false }))];
    });
  }

  async function remove(address: Address): Promise<void> {
    setPendingId(address.id);
    setActionFailure(null);
    const outcome = await deleteAddress(address.id);
    setPendingId(null);
    setConfirmingId(null);

    if (!outcome.ok) {
      setActionFailure(messageForFailure(outcome.status, outcome.message));
      return;
    }

    // Re-read rather than splice the row out: deleting the default promotes the oldest survivor, so
    // the result is not the old list minus one, and working out which address is now the default here
    // would be a second implementation of a rule the API already holds.
    await load();
  }

  async function submit(values: AddressValues): Promise<ApiFailure | null> {
    const outcome =
      editing.mode === "editing"
        ? await updateAddress(editing.address.id, toUpdatePayload(values))
        : await createAddress(toCreatePayload(values));

    if (!outcome.ok) {
      return outcome;
    }

    setEditing({ mode: "closed" });
    await load();
    return null;
  }

  if (loadFailure !== null) {
    return (
      <div
        role="alert"
        className="mt-6 rounded-2xl border border-border bg-surface px-8 py-12 text-center"
      >
        <p className="mx-auto max-w-measure text-muted">{loadFailure}</p>
        <button
          type="button"
          onClick={() => void load()}
          className="mt-6 inline-flex min-h-11 items-center rounded-lg border border-border px-6"
        >
          Try again
        </button>
      </div>
    );
  }

  if (addresses === null) {
    return <p className="mt-6 text-muted">Loading your addresses…</p>;
  }

  const defaultControl: DefaultControl =
    editing.mode === "editing" ? "none" : addresses.length === 0 ? "first" : "checkbox";

  return (
    <div>
      {actionFailure !== null && (
        <p
          role="alert"
          className="mt-6 rounded-lg border border-danger bg-surface px-4 py-3 text-sm text-danger"
        >
          {actionFailure}
        </p>
      )}

      {editing.mode !== "closed" && (
        <AddressForm
          // Keyed by the row it is editing so switching addresses remounts it: without this the
          // inputs would keep the text of the address the customer just left.
          key={editing.mode === "editing" ? editing.address.id : "new"}
          initial={editing.mode === "editing" ? editing.address : null}
          submitLabel={editing.mode === "editing" ? "Save address" : "Add address"}
          defaultControl={defaultControl}
          onSubmit={submit}
          onCancel={() => setEditing({ mode: "closed" })}
        />
      )}

      {editing.mode === "closed" && (
        <>
          {addresses.length === 0 ? (
            <EmptyState
              title="No addresses yet"
              description="Add a delivery address and it will be waiting the next time you check out."
            />
          ) : (
            <ul className="mt-6 flex flex-col gap-4">
              {addresses.map((address) => {
                const pending = pendingId === address.id;

                return (
                  <li key={address.id} className="rounded-2xl border border-border bg-surface p-6">
                    <div className="flex flex-wrap items-start justify-between gap-4">
                      <div>
                        <h3 className="text-lg">
                          {headingFor(address)}
                          {address.is_default && (
                            // A word, not a colour: `SCOPE.md` NFR-2 forbids signalling state with
                            // colour alone, and "which one will checkout use" is the one thing a
                            // customer scans this list for.
                            <span className="ml-3 rounded-lg border border-border px-2 py-0.5 align-middle text-xs text-muted">
                              Default
                            </span>
                          )}
                        </h3>
                        <address className="mt-2 text-sm not-italic text-muted">
                          {addressLines(address).map((line, index) => (
                            <span key={`${String(index)}-${line}`} className="block">
                              {line}
                            </span>
                          ))}
                        </address>
                      </div>

                      <div className="flex flex-wrap items-center gap-4 text-sm">
                        {!address.is_default && (
                          <button
                            type="button"
                            onClick={() => void makeDefault(address)}
                            disabled={pending}
                            className="min-h-11 text-primary underline disabled:opacity-60"
                          >
                            Make default
                          </button>
                        )}
                        <button
                          type="button"
                          onClick={() => {
                            setConfirmingId(null);
                            setEditing({ mode: "editing", address });
                          }}
                          disabled={pending}
                          className="min-h-11 text-primary underline disabled:opacity-60"
                        >
                          Edit
                        </button>
                        <button
                          type="button"
                          onClick={() => setConfirmingId(address.id)}
                          disabled={pending}
                          className="min-h-11 text-primary underline disabled:opacity-60"
                        >
                          Remove
                        </button>
                      </div>
                    </div>

                    {/* An inline confirmation rather than a browser dialog: it needs no focus trap,
                        it is keyboard-operable as it stands, and it says what is being removed
                        rather than asking about "this address" in a box of its own. */}
                    {confirmingId === address.id && (
                      <div className="mt-4 flex flex-wrap items-center gap-4 border-t border-border pt-4 text-sm">
                        <p>Remove this address?</p>
                        <button
                          type="button"
                          onClick={() => void remove(address)}
                          disabled={pending}
                          className="min-h-11 text-danger underline disabled:opacity-60"
                        >
                          {pending ? "Removing…" : "Yes, remove it"}
                        </button>
                        <button
                          type="button"
                          onClick={() => setConfirmingId(null)}
                          className="min-h-11 text-primary underline"
                        >
                          Keep it
                        </button>
                      </div>
                    )}
                  </li>
                );
              })}
            </ul>
          )}

          <button
            type="button"
            onClick={() => setEditing({ mode: "adding" })}
            className="mt-6 min-h-11 rounded-lg border border-border bg-surface px-6"
          >
            {addresses.length === 0 ? "Add your first address" : "Add an address"}
          </button>
        </>
      )}
    </div>
  );
}
